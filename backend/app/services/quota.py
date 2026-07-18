"""Kullanıcı başına günlük AI çağrı kotası (beta koruması).

OpenRouter ücretsiz katmanının günlük limiti paylaşımlı — tek kullanıcının
tüketmesini engeller. Limit AI_DAILY_LIMIT env değişkeniyle ayarlanır.
"""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.messages import msg
from ..models.tables import AiUsage, User


def consume_ai_quota(db: Session, user: User) -> None:
    """Bir AI çağrısı hakkı düşer; limit aşıldıysa 429 fırlatır (commit çağıranın)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = db.execute(
        select(AiUsage).where(AiUsage.user_id == user.id, AiUsage.day == today)
    ).scalar_one_or_none()
    if usage is None:
        usage = AiUsage(user_id=user.id, day=today, count=0)
        db.add(usage)
    if usage.count >= get_settings().ai_daily_limit:
        raise HTTPException(
            status_code=429, detail=msg("ai_quota_exhausted", user.language)
        )
    usage.count += 1
