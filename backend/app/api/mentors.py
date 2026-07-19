"""Faz 2: Mentorluk pazarı (havuz, ödemesiz beta).

Tüm uçlar mentor_market_enabled flag'i arkasında (kapalıyken 404 — uç var
olduğunu bile söylemez). Eşleştirme DB tabanlı: istek anında onaylı + müsait
mentorlardan rastgele atanır; müsait mentor yoksa jeton harcanmadan 409.
48 saat cevapsız istek, erişim anında tembel kontrolle expired + jeton iadesi.
"""

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import get_settings
from ..core.messages import msg
from ..db import get_db
from ..models.tables import (
    MentorProfile,
    MentorshipRequest,
    Submission,
    User,
)
from ..services import jetons
from ..services.push import send_push

REQUEST_TIMEOUT = timedelta(hours=48)

router = APIRouter(tags=["mentors"])


def require_mentor_market() -> None:
    if not get_settings().mentor_market_enabled:
        raise HTTPException(status_code=404, detail="Not Found")


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail=msg("admin_only", user.language))
    return user


def _expire_stale(db: Session, requests: list[MentorshipRequest]) -> None:
    """Tembel zaman aşımı: 48 saati geçen atanmış istekler expired + iade.
    Çağıran commit eder."""
    cutoff = datetime.now(timezone.utc) - REQUEST_TIMEOUT
    for r in requests:
        assigned = r.assigned_at
        if assigned is not None and assigned.tzinfo is None:  # sqlite naive döner
            assigned = assigned.replace(tzinfo=timezone.utc)
        if r.status == "assigned" and assigned is not None and assigned < cutoff:
            r.status = "expired"
            student = db.get(User, r.student_id)
            if student is not None:
                jetons.refund(db, student, r)
                send_push(
                    student,
                    msg("push_request_refunded_title", student.language),
                    msg("push_request_refunded_body", student.language, count=r.jeton_cost),
                )


def _mentor_stats(db: Session, user_ids: list[int]) -> dict[int, tuple[float | None, int]]:
    """mentor user_id → (ortalama rating, cevaplanan istek sayısı)."""
    if not user_ids:
        return {}
    rows = db.execute(
        select(
            MentorshipRequest.mentor_id,
            func.avg(MentorshipRequest.rating),
            func.count(MentorshipRequest.id),
        )
        .where(
            MentorshipRequest.mentor_id.in_(user_ids),
            MentorshipRequest.status == "answered",
        )
        .group_by(MentorshipRequest.mentor_id)
    ).all()
    return {mid: (float(avg) if avg is not None else None, count) for mid, avg, count in rows}


def _profile_json(p: MentorProfile, display_name: str, stats: tuple[float | None, int]) -> dict:
    avg, answered = stats
    return {
        "id": p.id,
        "user_id": p.user_id,
        "display_name": display_name,
        "bio": p.bio,
        "styles": p.styles,
        "portfolio_submission_ids": p.portfolio_submission_ids,
        "is_available": p.is_available,
        "rating": round(avg, 1) if avg is not None else None,
        "answered_count": answered,
    }


# ---------- Öğrenci tarafı ----------


@router.get("/mentors", dependencies=[Depends(require_mentor_market)])
def list_mentors(
    style: str | None = None,
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Onaylı mentorlar; stil filtresi + ad/bio araması, rating'e göre sıralı."""
    rows = db.execute(
        select(MentorProfile, User.display_name)
        .join(User, User.id == MentorProfile.user_id)
        .where(MentorProfile.status == "approved")
    ).all()
    if style:
        rows = [r for r in rows if style in (r[0].styles or [])]
    if q:
        needle = q.strip().lower()
        rows = [
            r for r in rows
            if needle in r[1].lower() or needle in (r[0].bio or "").lower()
        ]
    stats = _mentor_stats(db, [r[0].user_id for r in rows])
    mentors = [
        _profile_json(p, name, stats.get(p.user_id, (None, 0))) for p, name in rows
    ]
    # Puanlılar önce (yüksekten düşüğe), sonra cevap sayısı
    mentors.sort(
        key=lambda m: (m["rating"] is not None, m["rating"] or 0, m["answered_count"]),
        reverse=True,
    )
    return {"mentors": mentors}


@router.get("/mentors/{profile_id}", dependencies=[Depends(require_mentor_market)])
def get_mentor(
    profile_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.get(MentorProfile, profile_id)
    if profile is None or profile.status != "approved":
        raise HTTPException(status_code=404, detail=msg("mentor_not_found", user.language))
    owner = db.get(User, profile.user_id)
    stats = _mentor_stats(db, [profile.user_id]).get(profile.user_id, (None, 0))
    return _profile_json(profile, owner.display_name if owner else "", stats)


POOL_COST = 1  # havuzdan rastgele mentor
DIRECT_COST = 3  # seçmeli mentorluk (Faz 3, CLAUDE.md §2.5)


class MentorRequestBody(BaseModel):
    """Boş gövde / mentor_id yoksa havuz; mentor_id (profil id) verilirse seçmeli."""

    mentor_id: int | None = None


@router.post(
    "/submissions/{submission_id}/mentor-request",
    dependencies=[Depends(require_mentor_market)],
)
def create_mentor_request(
    submission_id: int,
    body: MentorRequestBody | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ödevi mentora gönderir: havuzdan rastgele (1 jeton) ya da mentor_id ile
    doğrudan seçilen mentora (3 jeton)."""
    submission = db.get(Submission, submission_id)
    if submission is None or submission.user_id != user.id:
        raise HTTPException(
            status_code=404, detail=msg("submission_not_found", user.language)
        )
    active = db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.submission_id == submission_id,
            MentorshipRequest.status == "assigned",
        )
    ).scalar_one_or_none()
    if active is not None:
        raise HTTPException(
            status_code=409, detail=msg("mentor_request_exists", user.language)
        )

    chosen_id = body.mentor_id if body is not None else None
    if chosen_id is not None:
        # Seçmeli: profil onaylı + müsait + kendisi değil, yoksa 409
        mentor_profile = db.get(MentorProfile, chosen_id)
        if mentor_profile is None or mentor_profile.status != "approved":
            raise HTTPException(
                status_code=404, detail=msg("mentor_not_found", user.language)
            )
        if not mentor_profile.is_available or mentor_profile.user_id == user.id:
            raise HTTPException(
                status_code=409, detail=msg("mentor_unavailable", user.language)
            )
        cost = DIRECT_COST
    else:
        candidates = db.execute(
            select(MentorProfile).where(
                MentorProfile.status == "approved",
                MentorProfile.is_available.is_(True),
                MentorProfile.user_id != user.id,  # kendi ödevine kendisi atanmasın
            )
        ).scalars().all()
        if not candidates:
            raise HTTPException(
                status_code=409, detail=msg("no_mentor_available", user.language)
            )
        mentor_profile = random.choice(candidates)
        cost = POOL_COST

    now = datetime.now(timezone.utc)
    request = MentorshipRequest(
        submission_id=submission_id,
        student_id=user.id,
        mentor_id=mentor_profile.user_id,
        jeton_cost=cost,
        status="assigned",
        assigned_at=now,
    )
    db.add(request)
    db.flush()  # request.id, transaction kaydına girsin
    jetons.spend(db, user, cost, request)  # yetersizse 402, hiçbir şey commit edilmez
    db.commit()

    mentor_user = db.get(User, mentor_profile.user_id)
    if mentor_user is not None:
        send_push(
            mentor_user,
            msg("push_new_request_title", mentor_user.language),
            msg("push_new_request_body", mentor_user.language, student=user.display_name),
        )
    return {
        "request_id": request.id,
        "mentor_display_name": mentor_user.display_name if mentor_user else "",
        "jeton_balance": user.jeton_balance,
    }


def _request_json(db: Session, r: MentorshipRequest) -> dict:
    mentor = db.get(User, r.mentor_id) if r.mentor_id else None
    return {
        "id": r.id,
        "submission_id": r.submission_id,
        "node_id": r.submission.node_id if r.submission else None,
        "status": r.status,
        "mentor_display_name": mentor.display_name if mentor else None,
        "feedback_text": r.feedback_text,
        "rating": r.rating,
        "created_at": r.created_at.isoformat(),
    }


@router.get("/mentor-requests", dependencies=[Depends(require_mentor_market)])
def my_requests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Öğrencinin istekleri (yeniden eskiye) — tembel zaman aşımı burada işler."""
    requests = db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.student_id == user.id)
        .order_by(MentorshipRequest.created_at.desc())
    ).scalars().all()
    _expire_stale(db, requests)
    db.commit()
    return {"requests": [_request_json(db, r) for r in requests]}


class RatingBody(BaseModel):
    rating: int = Field(ge=1, le=5)


@router.post(
    "/mentor-requests/{request_id}/rating",
    dependencies=[Depends(require_mentor_market)],
)
def rate_request(
    request_id: int,
    body: RatingBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.get(MentorshipRequest, request_id)
    if r is None or r.student_id != user.id:
        raise HTTPException(status_code=404, detail=msg("request_not_found", user.language))
    if r.status != "answered":
        raise HTTPException(
            status_code=409, detail=msg("request_not_answered", user.language)
        )
    if r.rating is not None:
        raise HTTPException(status_code=409, detail=msg("already_rated", user.language))
    r.rating = body.rating
    db.commit()
    return {"request_id": r.id, "rating": r.rating}


# ---------- Mentor tarafı ----------


class ApplyBody(BaseModel):
    bio: str = ""
    styles: list[str] = []
    portfolio_submission_ids: list[int] = []


@router.post("/mentors/apply", dependencies=[Depends(require_mentor_market)])
def apply_mentor(
    body: ApplyBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mentor başvurusu. Reddedilmişse günceller ve yeniden değerlendirmeye alır;
    bekleyen/onaylı başvuru varsa 409."""
    for sid in body.portfolio_submission_ids:
        s = db.get(Submission, sid)
        if s is None or s.user_id != user.id:
            raise HTTPException(
                status_code=422, detail=msg("portfolio_not_yours", user.language)
            )

    existing = db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user.id)
    ).scalar_one_or_none()
    if existing is not None and existing.status in ("pending", "approved"):
        raise HTTPException(
            status_code=409, detail=msg("mentor_apply_exists", user.language)
        )

    profile = existing or MentorProfile(user_id=user.id)
    profile.bio = body.bio
    profile.styles = body.styles
    profile.portfolio_submission_ids = body.portfolio_submission_ids
    profile.status = "pending"
    if existing is None:
        db.add(profile)
    # Portfolyo eserleri vitrine çıkar — herkes görebilmeli
    for sid in body.portfolio_submission_ids:
        db.get(Submission, sid).is_public = True
    db.commit()
    return {"status": profile.status}


@router.get("/mentor/me", dependencies=[Depends(require_mentor_market)])
def mentor_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user.id)
    ).scalar_one_or_none()
    if profile is None:
        return {"status": None}
    return {
        "status": profile.status,
        "is_available": profile.is_available,
        "bio": profile.bio,
        "styles": profile.styles,
    }


class AvailabilityBody(BaseModel):
    is_available: bool


def _approved_profile(db: Session, user: User) -> MentorProfile:
    profile = db.execute(
        select(MentorProfile).where(
            MentorProfile.user_id == user.id, MentorProfile.status == "approved"
        )
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=403, detail=msg("mentor_not_approved", user.language)
        )
    return profile


@router.patch("/mentor/me", dependencies=[Depends(require_mentor_market)])
def set_availability(
    body: AvailabilityBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _approved_profile(db, user)
    profile.is_available = body.is_available
    db.commit()
    return {"is_available": profile.is_available}


@router.get("/mentor/queue", dependencies=[Depends(require_mentor_market)])
def mentor_queue(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mentora atanmış, cevap bekleyen istekler — öğrenci çizimi + AI analizi bağlamıyla."""
    _approved_profile(db, user)
    requests = db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.mentor_id == user.id)
        .order_by(MentorshipRequest.created_at.desc())
    ).scalars().all()
    _expire_stale(db, requests)
    db.commit()
    out = []
    for r in requests:
        if r.status not in ("assigned", "answered"):
            continue
        student = db.get(User, r.student_id)
        out.append(
            {
                "id": r.id,
                "submission_id": r.submission_id,
                "node_id": r.submission.node_id if r.submission else None,
                "status": r.status,
                "student_display_name": student.display_name if student else "",
                "ai_result": r.submission.ai_result if r.submission else None,
                "created_at": r.created_at.isoformat(),
            }
        )
    return {"requests": out}


class FeedbackBody(BaseModel):
    feedback_text: str


@router.post(
    "/mentor-requests/{request_id}/feedback",
    dependencies=[Depends(require_mentor_market)],
)
def give_feedback(
    request_id: int,
    body: FeedbackBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.get(MentorshipRequest, request_id)
    if r is None:
        raise HTTPException(status_code=404, detail=msg("request_not_found", user.language))
    if r.mentor_id != user.id:
        raise HTTPException(status_code=403, detail=msg("not_request_mentor", user.language))
    _expire_stale(db, [r])
    db.commit()  # zaman aşımı işlediyse iade kalıcı olsun (409 dönsek bile)
    if r.status != "assigned":
        raise HTTPException(
            status_code=409, detail=msg("request_expired", user.language)
        )
    if not body.feedback_text.strip():
        raise HTTPException(status_code=422, detail=msg("feedback_empty", user.language))
    r.feedback_text = body.feedback_text.strip()
    r.status = "answered"
    r.answered_at = datetime.now(timezone.utc)
    db.commit()
    student = db.get(User, r.student_id)
    if student is not None:
        send_push(
            student,
            msg("push_feedback_ready_title", student.language),
            msg("push_feedback_ready_body", student.language, mentor=user.display_name),
        )
    return {"request_id": r.id, "status": r.status}


# ---------- Admin ----------


@router.get("/admin/mentor-applications", dependencies=[Depends(require_mentor_market)])
def list_applications(
    admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    rows = db.execute(
        select(MentorProfile, User.display_name)
        .join(User, User.id == MentorProfile.user_id)
        .where(MentorProfile.status == "pending")
        .order_by(MentorProfile.created_at)
    ).all()
    return {
        "applications": [
            {
                "id": p.id,
                "display_name": name,
                "bio": p.bio,
                "styles": p.styles,
                "portfolio_submission_ids": p.portfolio_submission_ids,
                "created_at": p.created_at.isoformat(),
            }
            for p, name in rows
        ]
    }


@router.post(
    "/admin/mentor-applications/{profile_id}/{decision}",
    dependencies=[Depends(require_mentor_market)],
)
def decide_application(
    profile_id: int,
    decision: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=404, detail="Not Found")
    profile = db.get(MentorProfile, profile_id)
    if profile is None:
        raise HTTPException(
            status_code=404, detail=msg("application_not_found", admin.language)
        )
    profile.status = "approved" if decision == "approve" else "rejected"
    db.commit()
    applicant = db.get(User, profile.user_id)
    if applicant is not None:
        key = "application_approved" if decision == "approve" else "application_rejected"
        send_push(
            applicant,
            msg(f"push_{key}_title", applicant.language),
            msg(f"push_{key}_body", applicant.language),
        )
    return {"id": profile.id, "status": profile.status}
