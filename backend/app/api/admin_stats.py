"""Beta sağlık panosu: tek curl ile temel metrikler (admin).

Mixpanel/Amplitude Faz 4 konusu — kapalı beta için DB'den sayımlar yeterli.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import (
    JetonTransaction,
    MentorshipRequest,
    Purchase,
    Submission,
    User,
    WaitlistSignup,
)
from .mentors import require_admin

router = APIRouter(tags=["admin"])


@router.get("/admin/stats")
def get_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    def _count(stmt) -> int:
        return db.execute(stmt).scalar_one()

    submissions_by_kind = dict(
        db.execute(
            select(Submission.kind, func.count()).group_by(Submission.kind)
        ).all()
    )
    requests_by_status = dict(
        db.execute(
            select(MentorshipRequest.status, func.count()).group_by(
                MentorshipRequest.status
            )
        ).all()
    )
    jetons_spent = _count(
        select(func.coalesce(func.sum(-JetonTransaction.delta), 0)).where(
            JetonTransaction.delta < 0
        )
    )

    return {
        "users_total": _count(select(func.count()).select_from(User)),
        "users_last_7d": _count(
            select(func.count()).select_from(User).where(User.created_at >= week_ago)
        ),
        "submissions_by_kind": submissions_by_kind,
        "submissions_last_7d": _count(
            select(func.count())
            .select_from(Submission)
            .where(Submission.created_at >= week_ago)
        ),
        "mentor_requests_by_status": requests_by_status,
        "jetons_spent_total": jetons_spent,
        "purchases_total": _count(select(func.count()).select_from(Purchase)),
        "waitlist_total": _count(select(func.count()).select_from(WaitlistSignup)),
    }
