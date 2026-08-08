"""AI çağrı hakkı: aktif ekonomiye göre günlük kota ya da jeton harcaması.

- ESKİ (jeton_ai_economy_enabled kapalı): kullanıcı başına GÜNLÜK sayaç
  (AiUsage). OpenRouter ücretsiz katmanı paylaşımlı olduğu için tek kullanıcının
  tüketmesini engelliyordu. Limit AI_DAILY_LIMIT.
- YENİ (bayrak açık): her AI aksiyonu jeton harcar (bkz. jetons.spend_for_ai).
  Günlük sayaç devre dışı; kıtlığı haftalık jeton tabanı yaratıyor.

Her iki yol da COMMIT ETMEZ. Bu kasıtlı: AI çağrısı 503 atarsa oturum commit'siz
kapanır (core/db.py) ve hak/jeton düşümü geri sarılır — başarısız AI çağrısı
kullanıcıya bedava kalır. Yeni ekonomide bu garanti daha da önemli, çünkü jeton
artık gerçek parayla alınabiliyor.
"""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.messages import msg
from ..models.tables import AiUsage, User
from . import jetons


def spend_ai(db: Session, user: User, cost: int, reason: str) -> None:
    """AI aksiyonu için hak düşer. Aktif ekonomiye göre dallanan tek giriş noktası.

    Yeni ekonomide `cost` 0 ise hiçbir şey harcanmaz (onboarding seviye belirleme
    ve ödev üretimi bilinçli ücretsiz — bkz. config.ai_cost_*). Bakiye yetmezse
    jetons.spend_for_ai 402 fırlatır; eski yolda limit dolarsa 429 gelir."""
    if not get_settings().jeton_ai_economy_enabled:
        consume_ai_quota(db, user)
        return
    if cost <= 0:
        return
    jetons.spend_for_ai(db, user, cost, reason)


def consume_ai_quota(db: Session, user: User) -> None:
    """Bir AI çağrısı hakkı düşer; limit aşıldıysa 429 fırlatır (commit çağıranın)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = db.execute(
        select(AiUsage).where(AiUsage.user_id == user.id, AiUsage.day == today)
    ).scalar_one_or_none()
    if usage is None:
        usage = AiUsage(user_id=user.id, day=today, count=0)
        db.add(usage)
    settings = get_settings()
    # Premium: yüksek günlük limit (dersler herkese açık, konfor paralı)
    from .billing import is_premium

    limit = settings.ai_daily_limit_premium if is_premium(user) else settings.ai_daily_limit
    if usage.count >= limit:
        raise HTTPException(
            status_code=429, detail=msg("ai_quota_exhausted", user.language)
        )
    usage.count += 1
