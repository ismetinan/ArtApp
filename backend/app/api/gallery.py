"""Topluluk galerisi (Faz 3): herkese açık paylaşılan çizimlerin akışı.

Kaynak: kullanıcının Gelişim Macerası'nda "herkese açık" yaptığı gönderiler
(varsayılan özel — CLAUDE.md §7.3). Görseller mevcut /submissions/{id}/image
ucundan servis edilir (is_public kontrolü orada zaten var).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import SkillNode, Submission, User
from .deps import get_current_user

router = APIRouter(tags=["gallery"])


@router.get("/gallery")
def get_gallery(
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Submission, User.display_name, SkillNode)
        .join(User, User.id == Submission.user_id)
        .outerjoin(SkillNode, SkillNode.id == Submission.node_id)
        .where(
            Submission.is_public.is_(True),
            Submission.kind.in_(("assignment", "free")),
        )
        .order_by(Submission.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    def _title(node: SkillNode | None) -> str | None:
        if node is None:
            return None
        if user.language == "en" and node.title_en:
            return node.title_en
        return node.title

    return {
        "items": [
            {
                "submission_id": s.id,
                "display_name": name,
                "node_title": _title(node),
                "is_mine": s.user_id == user.id,
                "created_at": s.created_at.isoformat(),
            }
            for s, name, node in rows
        ]
    }
