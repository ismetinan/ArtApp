"""Play Billing doğrulama servisi (hibrit model: jeton paketleri + Premium).

Satın alma asla istemci beyanıyla işlenmez: purchase_token her zaman Google Play
Developer API'ye doğrulatılır (para/güven akışı, CLAUDE.md §6). purchase_token'ın
unique Purchase satırı çifte hak vermeyi engeller. Abonelikte token yenilemelerde
sabit kalır; her yeni fatura dönemi görüldüğünde aylık jeton bir kez verilir.

Testler `verify_product_with_play` / `verify_subscription_with_play` /
`acknowledge_with_play` fonksiyonlarını monkeypatch'ler — gerçek ağ çağrısı yok.
"""

import json
import logging
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.messages import msg
from ..models.tables import Purchase, User
from . import apple_iap, jetons

log = logging.getLogger(__name__)

# Ürün kataloğu — Play Console'daki kimliklerle birebir aynı olmalı (DEPLOY.md §9)
JETON_PRODUCTS = {"jeton_5": 5, "jeton_15": 15, "jeton_40": 40}
SUBSCRIPTION_PRODUCT = "premium_monthly"

_API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"


class PlayVerifyError(Exception):
    """Play API token'ı geçersiz/iptal saydı ya da satın alma tamamlanmamış."""


class BillingConfigError(Exception):
    """PLAY_SERVICE_ACCOUNT_JSON eksik/bozuk ya da Play API'ye ulaşılamıyor —
    kullanıcı hatası değil, operatör yapılandırması. Uçlar 503'e çevirir."""


def is_premium(user: User) -> bool:
    until = user.premium_until
    if until is None:
        return False
    if until.tzinfo is None:  # sqlite naive döner
        until = until.replace(tzinfo=timezone.utc)
    return until > datetime.now(timezone.utc)


def _access_token() -> str:
    sa_json = get_settings().play_service_account_json
    if not sa_json:
        raise BillingConfigError("PLAY_SERVICE_ACCOUNT_JSON boş")
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    try:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_json),
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
        creds.refresh(Request())
    except Exception as e:  # bozuk JSON, geçersiz anahtar, ağ hatası...
        raise BillingConfigError(f"service account yüklenemedi: {e}") from e
    return creds.token


def _play_call(method: str, path: str) -> dict:
    pkg = get_settings().android_package_name
    r = httpx.request(
        method,
        f"{_API}/{pkg}{path}",
        headers={"Authorization": f"Bearer {_access_token()}"},
        timeout=15,
    )
    if r.status_code in (400, 404, 410):
        raise PlayVerifyError(f"Play API {r.status_code}: {r.text[:200]}")
    r.raise_for_status()
    return r.json() if r.text else {}


def verify_product_with_play(product_id: str, token: str) -> dict:
    """purchases.products.get — purchaseState 0 (satın alındı) olmalı."""
    data = _play_call("GET", f"/purchases/products/{product_id}/tokens/{token}")
    if data.get("purchaseState") != 0:
        raise PlayVerifyError(f"purchaseState={data.get('purchaseState')}")
    return data


def verify_subscription_with_play(token: str) -> dict:
    """purchases.subscriptionsv2.get — aktif abonelik + dönem bitişini döndürür."""
    data = _play_call("GET", f"/purchases/subscriptionsv2/tokens/{token}")
    state = data.get("subscriptionState")
    if state not in ("SUBSCRIPTION_STATE_ACTIVE", "SUBSCRIPTION_STATE_IN_GRACE_PERIOD"):
        raise PlayVerifyError(f"subscriptionState={state}")
    return data


def acknowledge_with_play(kind: str, product_id: str, token: str) -> None:
    """Sunucudan acknowledge — 3 gün içinde yapılmazsa Google iade eder.
    Hata akışı bozmaz (istemci completePurchase ile de acknowledge edebilir)."""
    try:
        if kind == "jeton":
            _play_call(
                "POST", f"/purchases/products/{product_id}/tokens/{token}:acknowledge"
            )
        else:
            _play_call(
                "POST",
                f"/purchases/subscriptions/{product_id}/tokens/{token}:acknowledge",
            )
    except Exception:  # noqa: BLE001 — hak zaten verildi, ack en iyi çaba
        log.warning("Play acknowledge başarısız (%s)", product_id, exc_info=True)


def _subscription_expiry(data: dict) -> datetime:
    items = data.get("lineItems") or []
    raw = items[0].get("expiryTime") if items else None
    if not raw:
        raise PlayVerifyError("expiryTime yok")
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _apply_subscription(
    db: Session, user: User, purchase: Purchase, data: dict
) -> None:
    """premium_until'i uzatır; yeni fatura dönemiyse aylık jetonu bir kez verir.

    Yeni ekonomide (jeton_ai_economy_enabled) aylık jeton YIĞINI verilmez —
    Premium'un karşılığı yüksek haftalık taban (weekly_jeton_floor_premium) +
    güçlü AI modeli. Yığın verilseydi Premium jetonu stoklardı ve "birikmez"
    kuralı delinirdi. Dönem takibi (granted_expiry) yine ilerler."""
    settings = get_settings()
    expiry = _subscription_expiry(data)
    granted = purchase.granted_expiry
    if granted is not None and granted.tzinfo is None:
        granted = granted.replace(tzinfo=timezone.utc)
    if granted is None or expiry > granted:
        monthly = 0 if settings.jeton_ai_economy_enabled else settings.premium_monthly_jetons
        if monthly > 0:  # grant() 0/negatif miktarda ValueError atar
            jetons.grant(db, user, monthly, "premium_monthly", paid=True)
        purchase.granted_expiry = expiry
    user.premium_until = expiry


def process_purchase(
    db: Session, user: User, product_id: str, token: str, platform: str = "android"
) -> Purchase:
    """Doğrular ve hakkı verir; idempotent. commit çağıranın sorumluluğunda.

    platform="ios" ise token, StoreKit 2'nin imzalı işlemi (JWS) olarak gelir ve
    Apple zinciriyle YEREL doğrulanır (bkz. services/apple_iap.py); saklanan
    "token" o işlemin transactionId'si olur. Geri kalan akış Play ile aynı:
    unique token çifte hak vermeyi engeller.
    """
    if platform == "ios":
        return _process_apple_purchase(db, user, product_id, token)
    if product_id in JETON_PRODUCTS:
        kind = "jeton"
    elif product_id == SUBSCRIPTION_PRODUCT:
        kind = "subscription"
    else:
        raise HTTPException(status_code=400, detail=msg("purchase_invalid", user.language))

    existing = db.execute(
        select(Purchase).where(Purchase.purchase_token == token)
    ).scalar_one_or_none()
    if existing is not None and existing.user_id != user.id:
        raise HTTPException(status_code=400, detail=msg("purchase_invalid", user.language))

    try:
        if kind == "jeton":
            if existing is not None:
                return existing  # jeton hakkı zaten verildi — tekrar yok
            verify_product_with_play(product_id, token)
            purchase = Purchase(
                user_id=user.id, product_id=product_id, purchase_token=token, kind=kind
            )
            db.add(purchase)
            db.flush()
            jetons.grant(db, user, JETON_PRODUCTS[product_id], "purchase", paid=True)
        else:
            data = verify_subscription_with_play(token)
            purchase = existing
            if purchase is None:
                purchase = Purchase(
                    user_id=user.id,
                    product_id=product_id,
                    purchase_token=token,
                    kind=kind,
                )
                db.add(purchase)
                db.flush()
            # Aynı token yeniden gelirse bu, yenileme kontrolüdür (lazy refresh)
            _apply_subscription(db, user, purchase, data)
    except PlayVerifyError as e:
        log.info("Satın alma doğrulanamadı: %s", e)
        raise HTTPException(
            status_code=400, detail=msg("purchase_invalid", user.language)
        ) from e
    except (BillingConfigError, httpx.HTTPError) as e:
        # Yapılandırma/Play API sorunu — kullanıcının suçu değil; hak verilmedi,
        # istemci "geri yükle" ile daha sonra tekrar dener.
        log.error("Billing yapılandırma/Play API hatası: %s", e)
        raise HTTPException(
            status_code=503, detail=msg("billing_unavailable", user.language)
        ) from e
    acknowledge_with_play(kind, product_id, token)
    return purchase


def refresh_subscription(db: Session, user: User) -> None:
    """Lazy yenileme: kayıtlı abonelik token'ını yeniden doğrular (Pub/Sub'sız v1).
    Doğrulama başarısızsa (iptal/expire) premium_until'e dokunmaz — süre kendi
    doğal bitişinde dolar. commit çağıranın sorumluluğunda."""
    purchase = db.execute(
        select(Purchase)
        .where(Purchase.user_id == user.id, Purchase.kind == "subscription")
        .order_by(Purchase.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if purchase is None:
        return
    try:
        data = verify_subscription_with_play(purchase.purchase_token)
        _apply_subscription(db, user, purchase, data)
    except (PlayVerifyError, BillingConfigError, HTTPException, httpx.HTTPError):
        return


def _process_apple_purchase(
    db: Session, user: User, product_id: str, jws: str
) -> Purchase:
    """App Store satın alması: imzalı işlemi doğrula, hakkı ver (idempotent).

    Play akışıyla aynı iskelet; farkı doğrulamanın ağ çağrısı değil yerel imza
    kontrolü olması. `transactionId` Purchase.purchase_token'a yazılır — unique
    olduğu için aynı işlem ikinci kez hak veremez.
    """
    if product_id in JETON_PRODUCTS:
        kind = "jeton"
    elif product_id == SUBSCRIPTION_PRODUCT:
        kind = "subscription"
    else:
        raise HTTPException(
            status_code=400, detail=msg("purchase_invalid", user.language)
        )

    try:
        tx = apple_iap.verify_transaction(jws, product_id)
    except apple_iap.AppleVerifyError as e:
        log.warning("Apple doğrulama başarısız: %s | %s", e, apple_iap.describe(jws))
        raise HTTPException(
            status_code=400, detail=msg("purchase_invalid", user.language)
        ) from e

    token = tx["transaction_id"]
    existing = db.execute(
        select(Purchase).where(Purchase.purchase_token == token)
    ).scalar_one_or_none()
    if existing is not None and existing.user_id != user.id:
        # Aynı işlem başka hesaba hak vermiş — paylaşılan makbuzla çoğaltma denemesi
        raise HTTPException(
            status_code=400, detail=msg("purchase_invalid", user.language)
        )

    if kind == "jeton":
        if existing is not None:
            return existing  # hak zaten verildi
        purchase = Purchase(
            user_id=user.id, product_id=product_id, purchase_token=token, kind=kind
        )
        db.add(purchase)
        db.flush()
        jetons.grant(db, user, JETON_PRODUCTS[product_id], "purchase", paid=True)
        return purchase

    # Abonelik: her yenilemede App Store yeni bir transactionId üretir, bu yüzden
    # dönem takibi granted_expiry ile yapılır (Play'deki mantığın aynısı).
    expiry = tx["expires_at"]
    if expiry is None:
        raise HTTPException(
            status_code=400, detail=msg("purchase_invalid", user.language)
        )
    purchase = existing
    if purchase is None:
        purchase = Purchase(
            user_id=user.id, product_id=product_id, purchase_token=token, kind=kind
        )
        db.add(purchase)
        db.flush()
    _apply_subscription_expiry(db, user, purchase, expiry)
    return purchase


def _apply_subscription_expiry(
    db: Session, user: User, purchase: Purchase, expiry: datetime
) -> None:
    """Play'deki _apply_subscription'ın sağlayıcıdan bağımsız hâli."""
    settings = get_settings()
    granted = purchase.granted_expiry
    if granted is not None and granted.tzinfo is None:
        granted = granted.replace(tzinfo=timezone.utc)
    if granted is None or expiry > granted:
        monthly = 0 if settings.jeton_ai_economy_enabled else settings.premium_monthly_jetons
        if monthly > 0:
            jetons.grant(db, user, monthly, "premium_monthly", paid=True)
        purchase.granted_expiry = expiry
    user.premium_until = expiry
