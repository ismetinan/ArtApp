"""Önleyici içerik filtresi (müşteri endişesi, 2026-07-19).

Bir görsel başka insanların önüne çıkmadan ÖNCE (herkese açık yapma, mentor
portfolyosu, mentor isteği) AI güvenlik kontrolünden geçer. Sonuç gönderi
başına bir kez hesaplanıp `submissions.moderation_status`'ta saklanır —
tekrar denemeler AI çağrısı yapmaz. Kullanıcının günlük AI kotasını YEMEZ
(platform koruması, kullanıcı hizmeti değil).

Tepkisel katman (bildir → admin kaldırır) yedek olarak aynen durur.
"""

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..ai import get_ai_provider
from ..core.messages import msg
from ..models.tables import Submission, User
from .storage import load_drawing

logger = logging.getLogger(__name__)


async def ensure_safe(db: Session, user: User, submission: Submission) -> None:
    """Görsel güvenli değilse yerelleştirilmiş 422 fırlatır; güvenliyse döner.

    unchecked → AI'a sorulur ve sonuç kalıcı yazılır (commit çağıranın).
    AI'a ulaşılamazsa 503: paylaşım kontrolsüz AÇILMAZ (fail-closed),
    kullanıcı daha sonra tekrar dener."""
    if submission.moderation_status == "safe":
        return
    if submission.moderation_status == "unsafe":
        raise HTTPException(status_code=422, detail=msg("content_unsafe", user.language))

    try:
        image = load_drawing(submission.file_path)
        verdict = await get_ai_provider().moderation_check(image)
    except Exception:
        logger.exception("Moderasyon kontrolü başarısız (submission=%s)", submission.id)
        raise HTTPException(status_code=503, detail=msg("ai_unavailable", user.language))

    if verdict.is_safe:
        submission.moderation_status = "safe"
        return
    submission.moderation_status = "unsafe"
    submission.is_public = False
    # Karar kalıcı: 422 üst katmanda rollback'e yol açmasın diye burada commit edilir
    db.commit()
    logger.warning(
        "Güvensiz içerik engellendi (submission=%s, kategori=%s, user=%s)",
        submission.id,
        verdict.category,
        user.id,
    )
    raise HTTPException(status_code=422, detail=msg("content_unsafe", user.language))
