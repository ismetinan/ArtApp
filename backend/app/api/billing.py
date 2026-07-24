"""Play Billing uçları (BILLING_ENABLED bayrağı arkasında — kapalıyken 404).

Akış: Flutter satın almayı Play'den tamamlar → purchase_token'ı buraya gönderir →
sunucu Play API'yle doğrular, hakkı verir (jeton/premium), acknowledge eder.
İstemci ancak 200 aldıktan sonra completePurchase çağırır.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db import get_db
from ..models.tables import User
from ..services import billing
from .deps import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


def require_billing() -> None:
    if not get_settings().billing_enabled:
        raise HTTPException(status_code=404, detail="Not Found")


class VerifyBody(BaseModel):
    product_id: str
    purchase_token: str


def _status_json(user: User) -> dict:
    return {
        "jeton_balance": user.jeton_balance,
        "gold_jeton_balance": user.jeton_paid_balance,  # satın alınan/Premium hediyesi
        "is_premium": billing.is_premium(user),
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "jeton_products": billing.JETON_PRODUCTS,
        "subscription_product": billing.SUBSCRIPTION_PRODUCT,
    }


@router.post("/verify", dependencies=[Depends(require_billing)])
def verify_purchase(
    body: VerifyBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    billing.process_purchase(db, user, body.product_id, body.purchase_token)
    db.commit()
    return _status_json(user)


@router.get("/status", dependencies=[Depends(require_billing)])
def billing_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Uygulama açılışında çağrılır: abonelik lazy yenilenir (Pub/Sub'sız v1)."""
    billing.refresh_subscription(db, user)
    db.commit()
    return _status_json(user)
