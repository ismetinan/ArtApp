"""App Store imzalı işlem doğrulaması.

En kritik test: SAHTE bir zincir reddedilmeli. Saldırgan kendi kök
sertifikasını üretip kendi imzaladığı bir işlemi gönderirse, kök parmak izi
kontrolü olmadan bu "geçerli" görünürdü ve bedava Premium alınırdı.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from app.services import apple_iap
from app.services.apple_iap import AppleVerifyError


def _key():
    return ec.generate_private_key(ec.SECP256R1())


def _cert(subject: str, key, issuer_name=None, issuer_key=None, ca=False):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
    issuer_name = issuer_name or name
    issuer_key = issuer_key or key
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(issuer_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
    )
    return builder.sign(issuer_key, hashes.SHA256())


def _der_b64(cert) -> str:
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()


def _make_jws(payload: dict, chain_certs, leaf_key) -> str:
    pem = leaf_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return jwt.encode(
        payload,
        pem,
        algorithm="ES256",
        headers={"x5c": [_der_b64(c) for c in chain_certs]},
    )


def _fake_apple_chain():
    """Saldırganın üretebileceği zincir: kendi kökü + ara + yaprak."""
    root_key, inter_key, leaf_key = _key(), _key(), _key()
    root = _cert("Sahte Root", root_key, ca=True)
    inter = _cert("Sahte Ara", inter_key, root.subject, root_key, ca=True)
    leaf = _cert("Sahte Yaprak", leaf_key, inter.subject, inter_key)
    return [leaf, inter, root], leaf_key


def _payload(**over):
    p = {
        "bundleId": "com.ismetinan.artapp",
        "productId": "jeton_15",
        "transactionId": "2000000123456789",
        "environment": "Production",
    }
    p.update(over)
    return p


# ---------- Güvenlik ----------


def test_forged_chain_is_rejected(client):
    """SAHTE kök → reddedilmeli. Bu kontrol olmadan bedava Premium alınırdı."""
    chain, leaf_key = _fake_apple_chain()
    jws = _make_jws(_payload(), chain, leaf_key)
    with pytest.raises(AppleVerifyError, match="Apple Root CA"):
        apple_iap.verify_transaction(jws, "jeton_15")


def test_missing_chain_is_rejected(client):
    _, leaf_key = _fake_apple_chain()
    pem = leaf_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    jws = jwt.encode(_payload(), pem, algorithm="ES256")  # x5c yok
    with pytest.raises(AppleVerifyError, match="x5c"):
        apple_iap.verify_transaction(jws, "jeton_15")


def test_garbage_token_is_rejected(client):
    with pytest.raises(AppleVerifyError):
        apple_iap.verify_transaction("bu-bir-jws-degil", "jeton_15")


# ---------- İş kuralları (imza doğrulaması atlanarak) ----------


@pytest.fixture
def signed(monkeypatch):
    """İmza zinciri doğrulamasını atlayıp payload kurallarını test etmeye yarar.
    Zincirin kendisi yukarıdaki testlerde ayrıca doğrulanıyor."""

    def use(payload):
        monkeypatch.setattr(apple_iap, "verify_signed_payload", lambda jws: payload)
        return "sahte.jws.token"

    return use


def test_bundle_id_must_match(client, signed):
    jws = signed(_payload(bundleId="com.baska.uygulama"))
    with pytest.raises(AppleVerifyError, match="bundleId"):
        apple_iap.verify_transaction(jws, "jeton_15")


def test_product_id_must_match(client, signed):
    """En ucuz paketi alıp en pahalısını istemek burada biter."""
    jws = signed(_payload(productId="jeton_5"))
    with pytest.raises(AppleVerifyError, match="productId"):
        apple_iap.verify_transaction(jws, "jeton_40")


def test_revoked_transaction_is_rejected(client, signed):
    """İade edilmiş işlem hak vermemeli."""
    jws = signed(_payload(revocationDate=1754600000000))
    with pytest.raises(AppleVerifyError, match="iptal"):
        apple_iap.verify_transaction(jws, "jeton_15")


def test_sandbox_rejected_in_production(client, signed):
    """Sandbox satın almasıyla bedava Premium alınmasın."""
    jws = signed(_payload(environment="Sandbox"))
    with pytest.raises(AppleVerifyError, match="sandbox"):
        apple_iap.verify_transaction(jws, "jeton_15")


def test_sandbox_allowed_when_enabled(client, signed, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ios_allow_sandbox_purchases", True)
    jws = signed(_payload(environment="Sandbox"))
    tx = apple_iap.verify_transaction(jws, "jeton_15")
    assert tx["transaction_id"] == "2000000123456789"


def test_valid_consumable(client, signed):
    tx = apple_iap.verify_transaction(signed(_payload()), "jeton_15")
    assert tx["is_subscription"] is False
    assert tx["expires_at"] is None


def test_valid_subscription_carries_expiry(client, signed):
    future = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000)
    jws = signed(_payload(productId="premium_monthly", expiresDate=future))
    tx = apple_iap.verify_transaction(jws, "premium_monthly")
    assert tx["is_subscription"] is True
    assert tx["expires_at"] > datetime.now(timezone.utc)


# ---------- Uçtan uca: /billing/verify iOS yolu ----------


@pytest.fixture
def ios_billing(monkeypatch):
    from app.core.config import get_settings
    from tests.test_billing import _enable_billing

    _enable_billing(monkeypatch)
    return get_settings()


def test_ios_purchase_grants_jetons(client, ios_billing, monkeypatch):
    from tests.test_mentors import _user

    monkeypatch.setattr(
        apple_iap,
        "verify_transaction",
        lambda jws, pid: {
            "transaction_id": "2000000999",
            "product_id": pid,
            "expires_at": None,
            "is_subscription": False,
            "environment": "Production",
        },
    )
    h, _ = _user(client, "iOSAlici")
    assert client.get("/profile", headers=h).json()["jeton_balance"] == 3

    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_15", "purchase_token": "jws", "platform": "ios"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["jeton_balance"] == 18
    assert r.json()["gold_jeton_balance"] == 15  # satın alınan = altın


def test_ios_purchase_replay_does_not_double_grant(client, ios_billing, monkeypatch):
    """Aynı işlem ikinci kez gönderilirse hak TEKRAR verilmemeli."""
    from tests.test_mentors import _user

    monkeypatch.setattr(
        apple_iap,
        "verify_transaction",
        lambda jws, pid: {
            "transaction_id": "2000000777",
            "product_id": pid,
            "expires_at": None,
            "is_subscription": False,
            "environment": "Production",
        },
    )
    h, _ = _user(client, "Tekrarci")
    body = {"product_id": "jeton_5", "purchase_token": "jws", "platform": "ios"}
    assert client.post("/billing/verify", json=body, headers=h).json()["jeton_balance"] == 8
    assert client.post("/billing/verify", json=body, headers=h).json()["jeton_balance"] == 8


def test_ios_transaction_cannot_be_reused_by_another_account(
    client, ios_billing, monkeypatch
):
    """Paylaşılan makbuzla ikinci hesaba hak çıkarılamaz."""
    from tests.test_mentors import _user

    monkeypatch.setattr(
        apple_iap,
        "verify_transaction",
        lambda jws, pid: {
            "transaction_id": "2000000555",
            "product_id": pid,
            "expires_at": None,
            "is_subscription": False,
            "environment": "Production",
        },
    )
    body = {"product_id": "jeton_5", "purchase_token": "jws", "platform": "ios"}
    h1, _ = _user(client, "Sahip")
    assert client.post("/billing/verify", json=body, headers=h1).status_code == 200
    h2, _ = _user(client, "Baskasi")
    assert client.post("/billing/verify", json=body, headers=h2).status_code == 400
    assert client.get("/profile", headers=h2).json()["jeton_balance"] == 3
