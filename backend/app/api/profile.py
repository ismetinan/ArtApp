from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..db import get_db
from ..models.tables import AbilityScore, Submission, User

router = APIRouter(tags=["profile"])


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
    return {
        "id": user.id,
        "display_name": user.display_name,
        "level": user.level,
        "xp": user.xp,
        "ability_chart": {s.axis: s.score for s in scores},
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
        raise HTTPException(status_code=404, detail="Gönderi bulunamadı")
    submission.is_public = body.is_public
    db.commit()
    return {"submission_id": submission.id, "is_public": submission.is_public}
