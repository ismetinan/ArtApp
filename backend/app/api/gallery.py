"""Topluluk galerisi (Faz 3): herkese açık paylaşılan çizimlerin akışı.

Kaynak: kullanıcının Gelişim Macerası'nda "herkese açık" yaptığı gönderiler
(varsayılan özel — CLAUDE.md §7.3). Görseller mevcut /submissions/{id}/image
ucundan servis edilir (is_public kontrolü orada zaten var).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..core.messages import msg
from ..db import get_db
from ..models.tables import ContentReport, SkillNode, Submission, User
from .deps import get_current_user
from .mentors import require_admin

router = APIRouter(tags=["gallery"])

REPORT_REASONS = ("uygunsuz", "spam", "telif", "diger")


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
            Submission.moderation_hidden.is_(False),
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


# ---------- UGC moderasyonu (Play politikası: bildir → incele → kaldır) ----------


class ReportBody(BaseModel):
    reason: str = "uygunsuz"


@router.post("/submissions/{submission_id}/report")
def report_submission(
    submission_id: int,
    body: ReportBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Herkese açık bir gönderiyi şikayet eder. Aynı kullanıcının ikinci
    şikayeti sessizce 200 döner (spam engeli)."""
    submission = db.get(Submission, submission_id)
    if submission is None or not submission.is_public:
        raise HTTPException(
            status_code=404, detail=msg("submission_not_found", user.language)
        )
    reason = body.reason if body.reason in REPORT_REASONS else "diger"
    exists = db.execute(
        select(ContentReport).where(
            ContentReport.submission_id == submission_id,
            ContentReport.reporter_id == user.id,
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            ContentReport(
                submission_id=submission_id, reporter_id=user.id, reason=reason
            )
        )
        db.commit()
    return {"ok": True}


@router.get("/admin/reports")
def list_reports(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Bekleyen şikayetler, gönderi başına gruplu (en çok şikayet edilen önce)."""
    rows = db.execute(
        select(
            ContentReport.submission_id,
            func.count().label("report_count"),
            func.max(ContentReport.created_at).label("last_report"),
        )
        .group_by(ContentReport.submission_id)
        .order_by(func.count().desc())
    ).all()
    items = []
    for submission_id, count, _last in rows:
        s = db.get(Submission, submission_id)
        if s is None:
            continue
        owner = db.get(User, s.user_id)
        reasons = [
            r[0]
            for r in db.execute(
                select(ContentReport.reason).where(
                    ContentReport.submission_id == submission_id
                )
            ).all()
        ]
        items.append(
            {
                "submission_id": submission_id,
                "owner_name": owner.display_name if owner else "?",
                "report_count": count,
                "reasons": reasons,
                "still_public": s.is_public and not s.moderation_hidden,
            }
        )
    return {"reports": items}


@router.post("/admin/reports/{submission_id}/{decision}")
def decide_report(
    submission_id: int,
    decision: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """hide: içerik galeriden kalıcı gizlenir (sahibi yeniden açamaz);
    dismiss: şikayetler temizlenir, içerik kalır."""
    if decision not in ("hide", "dismiss"):
        raise HTTPException(status_code=404, detail="Not Found")
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=404, detail=msg("submission_not_found", admin.language)
        )
    if decision == "hide":
        submission.is_public = False
        submission.moderation_hidden = True
    db.execute(
        delete(ContentReport).where(ContentReport.submission_id == submission_id)
    )
    db.commit()
    return {"submission_id": submission_id, "decision": decision}
