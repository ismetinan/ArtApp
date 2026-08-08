"""App Store satın alma doğrulaması (StoreKit 2 imzalı işlem — JWS).

Neden yerel doğrulama: iOS'ta `in_app_purchase` eklentisi bize StoreKit 2'nin
**imzalı işlemini** (JWS) veriyor. Apple bunun sunucuda YEREL olarak
doğrulanmasını destekliyor — imza zinciri Apple kök sertifikasına kadar
kontrol edilir. Böylece App Store Server API'ye ağ çağrısı yapmaya ve ayrı bir
`.p8` in-app purchase anahtarı taşımaya gerek kalmıyor: doğrulama için
saklanacak yeni bir sır YOK.

Play tarafıyla simetri: `billing.py` içindeki akış aynen korunuyor —
istemci token'ı gönderir, sunucu doğrular, hakkı sunucu verir, `Purchase`
satırındaki unique token çifte hak vermeyi engeller (para/güven akışı,
CLAUDE.md §6). iOS'ta "token" olarak işlemin `transactionId`'si kullanılır.

Güvenlik notu: JWS'in payload'ına doğrulamadan ASLA güvenilmez — imza zinciri
doğrulanmadan hiçbir alan okunmaz. Zincir: yaprak sertifika → ara sertifika →
Apple Root CA G3 (aşağıda sabit olarak gömülü, indirilmiyor).
"""

import base64
import json
import logging
from datetime import datetime, timezone

import jwt
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from ..core.config import get_settings

log = logging.getLogger(__name__)

# Apple Root CA - G3 (https://www.apple.com/certificateauthority/).
# Sabit gömülü: çalışma anında indirmek, indirmeyi ele geçiren birinin
# doğrulamayı tamamen atlatmasına izin verirdi.
APPLE_ROOT_CA_G3_PEM = b"""-----BEGIN CERTIFICATE-----
MIICQzCCAcmgAwIBAgIILcX8iNLFS5UwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwS
QXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9u
IEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcN
MTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBS
b290IENBIC0gRzMxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9y
aXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49
AgEGBSuBBAAiA2IABJjpLz1AcqTtkyJygRMc3RCV8cWjTnHcFBbZDuWmBSp3ZHtf
TjjTuxxEtX/1H7YyYl3J6YRbTzBPEVoA/VhYDKX1DyxNB0cTddqXl5dvMVztK517
IDvYuVTZXpmkOlEKMaNCMEAwHQYDVR0OBBYEFLuw3qFYM4iapIqZ3r6966/ayySr
MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAoGCCqGSM49BAMDA2gA
MGUCMQCD6cHEFl4aXTQY2e3v9GwOAEZLuN+yRhHFD/3meoyhpmvOwgPUnPWTxnS4
at+qIxUCMG1mihDK1A3UT82NQz60imOlM27jbdoXt2QfyFMm+YhidDkLF1vLUagM
6BgD56KyKA==
-----END CERTIFICATE-----"""


class AppleVerifyError(Exception):
    """İmza/zincir geçersiz ya da payload beklenenle uyuşmuyor."""


def _load_chain(x5c: list[str]) -> list[x509.Certificate]:
    """JWS başlığındaki x5c (base64 DER, yaprak önce) → sertifika listesi."""
    try:
        return [x509.load_der_x509_certificate(base64.b64decode(c)) for c in x5c]
    except Exception as e:
        raise AppleVerifyError(f"x5c çözülemedi: {e}") from e


def _verify_signed_by(child: x509.Certificate, parent: x509.Certificate) -> None:
    """child sertifikasının parent tarafından imzalandığını doğrular."""
    pub = parent.public_key()
    if not isinstance(pub, ec.EllipticCurvePublicKey):
        raise AppleVerifyError("beklenmeyen anahtar tipi (EC değil)")
    try:
        pub.verify(
            child.signature,
            child.tbs_certificate_bytes,
            ec.ECDSA(child.signature_hash_algorithm),
        )
    except InvalidSignature as e:
        raise AppleVerifyError("sertifika zinciri imzası geçersiz") from e


def _check_validity(cert: x509.Certificate, now: datetime) -> None:
    if not (cert.not_valid_before_utc <= now <= cert.not_valid_after_utc):
        raise AppleVerifyError("sertifika geçerlilik tarihi dışında")


def verify_signed_payload(jws: str) -> dict:
    """İmzalı işlemi doğrular ve payload'ı döndürür.

    Doğrulama sırası kritik: önce zincir Apple köküne bağlanır, sonra imza
    yaprak sertifikanın anahtarıyla kontrol edilir. Ancak ondan sonra
    payload okunur.
    """
    try:
        header = jwt.get_unverified_header(jws)
    except Exception as e:
        raise AppleVerifyError(f"JWS başlığı okunamadı: {e}") from e

    x5c = header.get("x5c")
    if not x5c or len(x5c) < 2:
        raise AppleVerifyError("x5c zinciri eksik")

    chain = _load_chain(x5c)
    leaf, root = chain[0], chain[-1]
    now = datetime.now(timezone.utc)

    # Zincirdeki kök, gömülü Apple kökünün AYNISI olmalı. Bu kontrol olmadan
    # saldırgan kendi kök sertifikasını zincire koyup kendi imzaladığı sahte
    # bir işlemi "geçerli" gösterebilirdi — doğrulamanın can damarı burası.
    apple_root = x509.load_pem_x509_certificate(APPLE_ROOT_CA_G3_PEM)
    if root.fingerprint(hashes.SHA256()) != apple_root.fingerprint(hashes.SHA256()):
        raise AppleVerifyError("kök sertifika Apple Root CA G3 değil")

    for cert in chain:
        _check_validity(cert, now)
    # Yapraktan köke doğru her halka bir üstü tarafından imzalanmış olmalı.
    # Kök zaten parmak iziyle sabitlendi; kendini imzalamasını ayrıca kontrol
    # etmek bir şey eklemez.
    for child, parent in zip(chain, chain[1:]):
        _verify_signed_by(child, parent)

    try:
        return jwt.decode(
            jws,
            key=leaf.public_key(),
            algorithms=["ES256"],
            options={"verify_aud": False, "verify_exp": False},
        )
    except Exception as e:
        raise AppleVerifyError(f"JWS imzası doğrulanamadı: {e}") from e


def verify_transaction(jws: str, expected_product_id: str) -> dict:
    """İmzalı işlemi doğrular ve iş kurallarını uygular.

    Döner: {transaction_id, product_id, expires_at, is_subscription}
    """
    payload = verify_signed_payload(jws)
    settings = get_settings()

    bundle_id = payload.get("bundleId")
    if bundle_id != settings.ios_bundle_id:
        raise AppleVerifyError(f"bundleId uyuşmuyor: {bundle_id!r}")

    product_id = payload.get("productId")
    if product_id != expected_product_id:
        # İstemcinin "ucuz paketi alıp pahalıyı istemesi" bu kontrolle biter
        raise AppleVerifyError(
            f"productId uyuşmuyor: {product_id!r} != {expected_product_id!r}"
        )

    if payload.get("revocationDate") or payload.get("revocationReason") is not None:
        raise AppleVerifyError("işlem iptal edilmiş (iade)")

    transaction_id = payload.get("transactionId")
    if not transaction_id:
        raise AppleVerifyError("transactionId yok")

    expires_ms = payload.get("expiresDate")
    expires_at = (
        datetime.fromtimestamp(expires_ms / 1000, tz=timezone.utc)
        if expires_ms
        else None
    )
    # Sandbox işlemleri prod'da hak vermemeli — test satın almalarıyla bedava
    # Premium alınmasının önü kapanıyor.
    environment = payload.get("environment", "Production")
    if not settings.ios_allow_sandbox_purchases and environment != "Production":
        raise AppleVerifyError(f"sandbox işlemi reddedildi (environment={environment})")

    return {
        "transaction_id": str(transaction_id),
        "product_id": product_id,
        "expires_at": expires_at,
        "is_subscription": expires_at is not None,
        "environment": environment,
    }


def describe(jws: str) -> str:
    """Teşhis için: imzayı doğrulamadan payload'ı özetler. ASLA hak vermek için
    kullanılmaz — yalnız log/hata ayıklama."""
    try:
        body = jws.split(".")[1]
        body += "=" * (-len(body) % 4)
        data = json.loads(base64.urlsafe_b64decode(body))
        return json.dumps(
            {k: data.get(k) for k in ("bundleId", "productId", "environment", "type")}
        )
    except Exception:
        return "<çözülemedi>"
