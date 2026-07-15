import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..ai import get_ai_provider, guard_assessment
from ..api.deps import get_current_user
from ..db import get_db
from ..models.tables import AbilityScore, Submission, User
from ..services.gamification import XP_PER_LEVEL
from ..services.quota import consume_ai_quota
from ..services.storage import save_drawing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/assess")
async def assess_level(
    files: list[UploadFile],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Onboarding 2-4. ekranlar: 3 çizim yükle → başlangıç seviyesi belirle."""
    if len(files) != 3:
        raise HTTPException(status_code=422, detail="Tam olarak 3 çizim yüklenmeli")
    consume_ai_quota(db, user)

    images: list[bytes] = []
    for f in files:
        content = await f.read()
        try:
            rel_path = save_drawing(content, f.filename or "cizim.png")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        images.append(content)
        db.add(Submission(user_id=user.id, kind="onboarding", file_path=rel_path))

    try:
        assessment = guard_assessment(await get_ai_provider().assess_level(images))
    except Exception:
        logger.exception("Seviye belirleme analizi başarısız (user=%s)", user.id)
        raise HTTPException(
            status_code=503,
            detail="AI şu an yanıt veremiyor, lütfen birazdan tekrar dene.",
        )

    # XP tabanını belirlenen seviyeye çek — yoksa ilk ödevden sonra
    # level_for_xp(xp) seviyeyi geri düşürür
    user.level = assessment.level
    user.xp = max(user.xp, (assessment.level - 1) * XP_PER_LEVEL)
    # Yeniden onboarding olursa eski skorlar sıfırdan yazılır
    db.query(AbilityScore).filter(AbilityScore.user_id == user.id).delete()
    for axis, score in assessment.ability_scores.items():
        db.add(AbilityScore(user_id=user.id, axis=axis.value, score=score))
    db.commit()

    return assessment
