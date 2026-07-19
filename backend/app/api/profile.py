import mimetypes

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.schemas import SkillAxis
from ..api.deps import get_current_user
from ..core.config import get_settings
from ..core.messages import msg
from ..db import get_db
from ..models.tables import AbilityScore, MentorProfile, Submission, User
from ..services.storage import load_drawing

router = APIRouter(tags=["profile"])


@router.get("/submissions/{submission_id}/image")
def get_submission_image(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Çizim dosyasını döner. Sadece sahibi — veya herkese açıksa herkes — görebilir."""
    submission = db.get(Submission, submission_id)
    if submission is None or (submission.user_id != user.id and not submission.is_public):
        raise HTTPException(status_code=404, detail=msg("submission_not_found", user.language))
    try:
        content = load_drawing(submission.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=msg("file_not_found", user.language))
    media_type = mimetypes.guess_type(submission.file_path)[0] or "image/jpeg"
    return Response(content=content, media_type=media_type)


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scores = db.execute(
        select(AbilityScore).where(AbilityScore.user_id == user.id)
    ).scalars().all()
    submissions = db.execute(
        select(Submission)
        .where(Submission.user_id == user.id, Submission.kind == "assignment")
        .order_by(Submission.created_at)
    ).scalars().all()
    score_map = {s.axis: s.score for s in scores}
    mentor = db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user.id)
    ).scalar_one_or_none()
    return {
        "id": user.id,
        "display_name": user.display_name,
        "level": user.level,
        "xp": user.xp,
        "language": user.language,
        "jeton_balance": user.jeton_balance,
        "mentor_market_enabled": get_settings().mentor_market_enabled,
        # Beta admini: Flutter buna bakarak başvuru onay panelini gösterir
        "is_admin": user.is_admin,
        # Faz 2: mentor rolü — Flutter buna bakarak paneli gösterir
        "mentor": None
        if mentor is None
        else {"status": mentor.status, "is_available": mentor.is_available},
        # Skor varsa 7 eksenin hepsi döner (eksikler 0) — radar chart hep tam çizilir.
        # Hiç skor yoksa boş kalır: onboarding yönlendirmesi buna bakıyor.
        "ability_chart": (
            {a.value: score_map.get(a.value, 0) for a in SkillAxis} if score_map else {}
        ),
        # "Gelişim Macerası": kronolojik, her ödev kendi AI notlarıyla
        "gelisim_macerasi": [
            {
                "submission_id": s.id,
                "node_id": s.node_id,
                "file_path": s.file_path,
                "ai_result": s.ai_result,
                "is_public": s.is_public,
                "created_at": s.created_at.isoformat(),
            }
            for s in submissions
        ],
    }


class PrivacyUpdate(BaseModel):
    is_public: bool


@router.patch("/submissions/{submission_id}/privacy")
def update_privacy(
    submission_id: int,
    body: PrivacyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = db.get(Submission, submission_id)
    if submission is None or submission.user_id != user.id:
        raise HTTPException(status_code=404, detail=msg("submission_not_found", user.language))
    submission.is_public = body.is_public
    db.commit()
    return {"submission_id": submission.id, "is_public": submission.is_public}
