"""Faz 2: Mentorluk pazarı (havuz, ödemesiz beta).

Tüm uçlar mentor_market_enabled flag'i arkasında (kapalıyken 404 — uç var
olduğunu bile söylemez). Eşleştirme DB tabanlı: istek anında onaylı + müsait
mentorlardan rastgele atanır; müsait mentor yoksa jeton harcanmadan 409.
48 saat cevapsız istek, erişim anında tembel kontrolle expired + jeton iadesi.
"""

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
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
from ..services import donations, earnings, jetons, moderation
from ..services.push import send_push

REQUEST_TIMEOUT = timedelta(hours=48)

# Mentor uzmanlık stilleri (müşteri isteği, 2026-08-08). `anime` ve `manga`
# eskiden ayrı anahtarlardı, artık tek kategori — eski profiller kırılmasın diye
# okuma ve filtrelemede eşleniyor, yazarken kanonik hâle çevriliyor.
# Flutter'daki styleLabels/styleCanonical ile birebir aynı olmalı.
STYLE_ALIASES = {"anime": "anime_manga", "manga": "anime_manga"}


def _canonical_styles(styles: list | None) -> list[str]:
    out: list[str] = []
    for s in styles or []:
        key = STYLE_ALIASES.get(s, s)
        if key not in out:  # anime+manga birleşince tekrar etmesin
            out.append(key)
    return out

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
            if student is None:
                continue
            # Yeni ekonomide mentorluk ücretsiz (jeton_cost=0): iade edilecek bir
            # şey yok ve "1 jeton iade edildi" bildirimi yanlış olur.
            if r.jeton_cost > 0:
                jetons.refund(db, student, r)
                send_push(
                    student,
                    msg("push_request_refunded_title", student.language),
                    msg("push_request_refunded_body", student.language, count=r.jeton_cost),
                    data={"route": "my_requests"},
                )
            else:
                send_push(
                    student,
                    msg("push_request_expired_title", student.language),
                    msg("push_request_expired_body", student.language),
                    data={"route": "my_requests"},
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


def _profile_json(
    p: MentorProfile,
    display_name: str,
    stats: tuple[float | None, int],
    include_donation: bool = False,
) -> dict:
    avg, answered = stats
    out = {
        "id": p.id,
        "user_id": p.user_id,
        "display_name": display_name,
        "bio": p.bio,
        "styles": _canonical_styles(p.styles),
        "portfolio_submission_ids": p.portfolio_submission_ids,
        "is_available": p.is_available,
        "rating": round(avg, 1) if avg is not None else None,
        "answered_count": answered,
    }
    # Bağış linki YALNIZ mentor profili detayında ve YALNIZ admin onayından
    # geçmişse döner. Listede bilinçli yok: liste kartında para vurgusu
    # mentorluğu "ücretli hizmet" gibi gösterir ve Apple §3.2.1'in "hiçbir şeyi
    # açmıyor / tamamen isteğe bağlı" çerçevesini zayıflatır.
    if include_donation and p.donation_url and p.donation_status == "approved":
        out["donation_url"] = p.donation_url
        out["donation_platform"] = p.donation_platform
    return out


# ---------- Öğrenci tarafı ----------


@router.get("/mentors", dependencies=[Depends(require_mentor_market)])
def list_mentors(
    style: str | None = Query(None, max_length=40),
    q: str | None = Query(None, max_length=100),
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
        # Filtre kanonik anahtarla gelir; eski kayıtlar eşlenerek karşılaştırılır
        wanted = STYLE_ALIASES.get(style, style)
        rows = [r for r in rows if wanted in _canonical_styles(r[0].styles)]
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
    return _profile_json(
        profile, owner.display_name if owner else "", stats, include_donation=True
    )


POOL_COST = 1  # havuzdan rastgele mentor (ESKİ ekonomi)
DIRECT_COST = 3  # seçmeli mentorluk (ESKİ ekonomi, Faz 3, CLAUDE.md §2.5)

# YENİ ekonomi: mentorluk ücretsiz. Spam'i para değil kota tutuyor (2026-08-08).
MAX_OPEN_REQUESTS = 3  # bir öğrencinin aynı anda açık istek sayısı
MENTOR_COOLDOWN = timedelta(hours=24)  # aynı öğrenci → aynı mentor
MENTOR_INBOX_CAP = 5  # bir mentorun aynı anda taşıyabileceği açık istek


def _open_request_count(db: Session, student_id: int) -> int:
    return int(
        db.execute(
            select(func.count(MentorshipRequest.id)).where(
                MentorshipRequest.student_id == student_id,
                MentorshipRequest.status == "assigned",
            )
        ).scalar_one()
    )


def _expire_stale_for_student(db: Session, student_id: int) -> None:
    """Öğrencinin açık isteklerinde tembel zaman aşımını çalıştırır.

    Kota kontrolünden ÖNCE şart: zaman aşımı yalnız erişim anında işliyor ve
    sadece 3 uçtan tetikleniyordu. Bu olmadan 48 saati geçmiş ama hâlâ 'assigned'
    görünen MAX_OPEN_REQUESTS kadar istek öğrenciyi kalıcı olarak kilitler.
    Yan fayda: iki taraf da ekranı açmazsa jetonun hiç iade edilmemesi hatası da
    burada kapanıyor."""
    stale = db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.student_id == student_id,
            MentorshipRequest.status == "assigned",
        )
    ).scalars().all()
    _expire_stale(db, stale)


def _cooldown_mentor_ids(db: Session, student_id: int) -> set[int]:
    """Son MENTOR_COOLDOWN içinde bu öğrenciden istek almış mentor user_id'leri."""
    cutoff = datetime.now(timezone.utc) - MENTOR_COOLDOWN
    rows = db.execute(
        select(MentorshipRequest.mentor_id).where(
            MentorshipRequest.student_id == student_id,
            MentorshipRequest.mentor_id.is_not(None),
            MentorshipRequest.created_at >= cutoff,
        )
    ).scalars().all()
    return {m for m in rows if m is not None}


def _full_inbox_mentor_ids(db: Session) -> set[int]:
    """Açık istek sayısı MENTOR_INBOX_CAP'e ulaşmış mentor user_id'leri.

    Mentorluk ücretsizleşince tek mentorun sınırsız istekle dolması gerçek bir
    risk; ayrıca 'seçmeli de bedavaysa herkes popüler mentora gider' sorununun
    cevabı da bu — dolan mentor havuz adaylığından düşer, öğrenci havuza yönelir."""
    rows = db.execute(
        select(MentorshipRequest.mentor_id, func.count(MentorshipRequest.id))
        .where(
            MentorshipRequest.status == "assigned",
            MentorshipRequest.mentor_id.is_not(None),
        )
        .group_by(MentorshipRequest.mentor_id)
        .having(func.count(MentorshipRequest.id) >= MENTOR_INBOX_CAP)
    ).all()
    return {mentor_id for mentor_id, _ in rows if mentor_id is not None}


class MentorRequestBody(BaseModel):
    """Boş gövde / mentor_id yoksa havuz; mentor_id (profil id) verilirse seçmeli."""

    mentor_id: int | None = None


@router.post(
    "/submissions/{submission_id}/mentor-request",
    dependencies=[Depends(require_mentor_market)],
)
async def create_mentor_request(
    submission_id: int,
    body: MentorRequestBody | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ödevi mentora gönderir: havuzdan rastgele ya da mentor_id ile seçmeli.

    ESKİ ekonomi: havuz 1 jeton, seçmeli 3 altın jeton.
    YENİ ekonomi: ikisi de ÜCRETSİZ; kötüye kullanımı üç kota tutuyor —
    aynı anda MAX_OPEN_REQUESTS açık istek, aynı mentora MENTOR_COOLDOWN'da bir,
    mentor başına MENTOR_INBOX_CAP açık istek."""
    free_mentorship = get_settings().jeton_ai_economy_enabled
    submission = db.get(Submission, submission_id)
    if submission is None or submission.user_id != user.id:
        raise HTTPException(
            status_code=404, detail=msg("submission_not_found", user.language)
        )
    # Önleyici filtre: bir insana (mentora) gidecek görsel önce güvenlik kontrolünden geçer
    await moderation.ensure_safe(db, user, submission)

    cooldown_ids: set[int] = set()
    full_inbox_ids: set[int] = set()
    if free_mentorship:
        # Sıra önemli: önce süresi geçmişleri düş, sonra say (bkz. yardımcı docstring)
        _expire_stale_for_student(db, user.id)
        db.commit()
        if _open_request_count(db, user.id) >= MAX_OPEN_REQUESTS:
            raise HTTPException(
                status_code=409,
                detail=msg(
                    "too_many_open_requests", user.language, count=MAX_OPEN_REQUESTS
                ),
            )
        cooldown_ids = _cooldown_mentor_ids(db, user.id)
        full_inbox_ids = _full_inbox_mentor_ids(db)

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
        # Seçmelide mentor belli → kotalar doğrudan kontrol edilebilir
        if mentor_profile.user_id in cooldown_ids:
            raise HTTPException(
                status_code=409, detail=msg("mentor_cooldown", user.language)
            )
        if mentor_profile.user_id in full_inbox_ids:
            raise HTTPException(
                status_code=409, detail=msg("mentor_busy", user.language)
            )
        cost = 0 if free_mentorship else DIRECT_COST
        gold_only = not free_mentorship  # eski model: seçmeli yalnız altınla
    else:
        candidates = db.execute(
            select(MentorProfile).where(
                MentorProfile.status == "approved",
                MentorProfile.is_available.is_(True),
                MentorProfile.user_id != user.id,  # kendi ödevine kendisi atanmasın
            )
        ).scalars().all()
        # Havuzda mentor SONRADAN rastgele atanıyor, bu yüzden kotalar önceden
        # kontrol edilemez — aday listesinden ÇIKARMA olarak uygulanır.
        candidates = [
            c
            for c in candidates
            if c.user_id not in cooldown_ids and c.user_id not in full_inbox_ids
        ]
        if not candidates:
            raise HTTPException(
                status_code=409, detail=msg("no_mentor_available", user.language)
            )
        mentor_profile = random.choice(candidates)
        cost = 0 if free_mentorship else POOL_COST
        gold_only = False  # havuz: önce-ücretsiz (ücretsiz jetonla da sorulabilir)

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
    if cost > 0:  # yeni ekonomide mentorluk ücretsiz → harcama yok
        jetons.spend(db, user, cost, request, gold_only=gold_only)  # yetersizse 402
    db.commit()

    mentor_user = db.get(User, mentor_profile.user_id)
    if mentor_user is not None:
        send_push(
            mentor_user,
            msg("push_new_request_title", mentor_user.language),
            msg("push_new_request_body", mentor_user.language, student=user.display_name),
            data={"route": "mentor_panel"},
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


MIN_SAMPLE_CRITIQUE = 200  # karakter — kalite kapısı
MENTOR_REAPPLY_COOLDOWN = timedelta(days=14)


class ApplyBody(BaseModel):
    bio: str = Field("", max_length=2000)
    styles: list[str] = Field(default_factory=list, max_length=10)
    portfolio_submission_ids: list[int] = Field(default_factory=list, max_length=12)
    # Kalite kapısı + bağış linki (yeni ekonomi). Eski istemciler bu alanları
    # göndermez; o yüzden varsayılanlı ve yalnız bayrak açıkken zorunlu.
    sample_critique: str = Field("", max_length=5000)
    rules_accepted: bool = False
    donation_url: str | None = Field(None, max_length=300)


@router.post("/mentors/apply", dependencies=[Depends(require_mentor_market)])
async def apply_mentor(
    body: ApplyBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mentor başvurusu. Reddedilmişse günceller ve yeniden değerlendirmeye alır;
    bekleyen/onaylı başvuru varsa 409."""
    new_economy = get_settings().jeton_ai_economy_enabled
    if new_economy:
        if not body.rules_accepted:
            raise HTTPException(
                status_code=422, detail=msg("mentor_rules_not_accepted", user.language)
            )
        if len(body.sample_critique.strip()) < MIN_SAMPLE_CRITIQUE:
            raise HTTPException(
                status_code=422,
                detail=msg(
                    "sample_critique_too_short", user.language, count=MIN_SAMPLE_CRITIQUE
                ),
            )
    try:
        donations.ensure_no_payment_details(body.bio, body.sample_critique)
    except donations.PaymentDetailsInTextError:
        raise HTTPException(
            status_code=422, detail=msg("no_payment_details_in_text", user.language)
        )
    try:
        donation_url, donation_platform = donations.normalize_donation_url(
            body.donation_url
        )
    except donations.DonationUrlError:
        raise HTTPException(
            status_code=422, detail=msg("donation_url_invalid", user.language)
        )

    for sid in body.portfolio_submission_ids:
        s = db.get(Submission, sid)
        if s is None or s.user_id != user.id:
            raise HTTPException(
                status_code=422, detail=msg("portfolio_not_yours", user.language)
            )
        # Portfolyo herkese açık olur — önce güvenlik kontrolü
        await moderation.ensure_safe(db, user, s)

    existing = db.execute(
        select(MentorProfile).where(MentorProfile.user_id == user.id)
    ).scalar_one_or_none()
    if existing is not None and existing.status in ("pending", "approved"):
        raise HTTPException(
            status_code=409, detail=msg("mentor_apply_exists", user.language)
        )
    # Ret sonrası bekleme: eskiden reddedilen profil sınırsız tekrar başvurabiliyordu
    if new_economy and existing is not None and existing.status == "rejected":
        rejected = existing.rejected_at
        if rejected is not None:
            if rejected.tzinfo is None:  # sqlite naive döner
                rejected = rejected.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - rejected < MENTOR_REAPPLY_COOLDOWN:
                raise HTTPException(
                    status_code=409,
                    detail=msg(
                        "reapply_too_soon",
                        user.language,
                        days=MENTOR_REAPPLY_COOLDOWN.days,
                    ),
                )

    profile = existing or MentorProfile(user_id=user.id)
    profile.bio = body.bio
    profile.styles = _canonical_styles(body.styles)
    profile.portfolio_submission_ids = body.portfolio_submission_ids
    profile.status = "pending"
    profile.sample_critique = body.sample_critique
    if body.rules_accepted:
        profile.rules_accepted_at = datetime.now(timezone.utc)
    # Bağış linki değiştiyse yeniden onaya düşer — onaysız link gösterilmez
    if donation_url != profile.donation_url:
        profile.donation_url = donation_url
        profile.donation_platform = donation_platform
        profile.donation_status = "pending" if donation_url else "rejected"
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
        "styles": _canonical_styles(profile.styles),
        "sample_critique": profile.sample_critique,
        # Mentor kendi linkini her zaman görür (onay beklerken de) — öğrenciye
        # yalnız onaylıysa gösterilir
        "donation_url": profile.donation_url,
        "donation_platform": profile.donation_platform,
        "donation_status": profile.donation_status,
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
        gold = r.paid_cost > 0  # gelir-destekli (altın) → öncelik + 'derin redline'
        out.append(
            {
                "id": r.id,
                "submission_id": r.submission_id,
                "node_id": r.submission.node_id if r.submission else None,
                "status": r.status,
                "student_display_name": student.display_name if student else "",
                "ai_result": r.submission.ai_result if r.submission else None,
                "gold": gold,
                "created_at": r.created_at.isoformat(),
            }
        )
    # Bekleyen altın (öncelikli) istekler kuyruğun başında; sonra en yeni.
    out.sort(key=lambda x: (x["status"] != "assigned", not x["gold"]))
    return {"requests": out}


@router.get("/mentor/stats", dependencies=[Depends(require_mentor_market)])
def mentor_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mentorun defter özeti: cevaplanan istek sayısı + puan (itibar).

    Yeni ekonomide para yok — mentora ödeme uygulama dışı isteğe bağlı bağışla
    ve %100 mentora gidiyor, Artora akışa girmiyor (bkz. /terms)."""
    _approved_profile(db, user)
    out = earnings.summary(db, user.id)
    rating, answered = _mentor_stats(db, [user.id]).get(user.id, (None, 0))
    out["rating"] = rating
    out["answered_requests"] = answered
    out["jeton_ai_economy"] = get_settings().jeton_ai_economy_enabled
    return out


@router.get("/mentor/earnings", dependencies=[Depends(require_mentor_market)])
def mentor_earnings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """DEPRECATED — /mentor/stats'ın eski adı. Eski istemciler kırılmasın diye bir
    sürüm daha duruyor. Gövde BİLİNÇLİ olarak eski şekliyle aynı kalıyor (yalnız
    earnings.summary): geriye dönük uç, yeni alanların taşındığı yer değil."""
    _approved_profile(db, user)
    return earnings.summary(db, user.id)


class FeedbackBody(BaseModel):
    feedback_text: str = Field(max_length=10_000)


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
    # Gelir paylaşımı (Faz A): cevaplanan istek mentora jeton-eşdeğeri kazanç yazar
    earnings.credit(db, user.id, r)
    db.commit()
    student = db.get(User, r.student_id)
    if student is not None:
        send_push(
            student,
            msg("push_feedback_ready_title", student.language),
            msg("push_feedback_ready_body", student.language, mentor=user.display_name),
            data={"route": "my_requests"},
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
                "styles": _canonical_styles(p.styles),
                "portfolio_submission_ids": p.portfolio_submission_ids,
                "created_at": p.created_at.isoformat(),
                # Kalite kapısı: admin kararını asıl buna bakarak verir
                "sample_critique": p.sample_critique,
                "rules_accepted": p.rules_accepted_at is not None,
                # Bağış linki ayrı onaylanır (ayrı uç) — başvuru onayı linki onaylamaz
                "donation_url": p.donation_url,
                "donation_platform": p.donation_platform,
                "donation_status": p.donation_status,
            }
            for p, name in rows
        ]
    }


@router.post(
    "/admin/mentor-profiles/{profile_id}/donation/{decision}",
    dependencies=[Depends(require_mentor_market)],
)
def decide_donation_link(
    profile_id: int,
    decision: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bağış bağlantısını onaylar/reddeder. Başvuru onayından AYRI: link sonradan
    da değiştirilebiliyor ve her değişiklik yeniden onaya düşüyor. Onaysız link
    mentor profilinde hiç gösterilmez (bkz. _profile_json)."""
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=404, detail="Not Found")
    profile = db.get(MentorProfile, profile_id)
    if profile is None:
        raise HTTPException(
            status_code=404, detail=msg("application_not_found", admin.language)
        )
    profile.donation_status = "approved" if decision == "approve" else "rejected"
    db.commit()
    return {"id": profile.id, "donation_status": profile.donation_status}


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
    if decision == "reject":
        profile.rejected_at = datetime.now(timezone.utc)  # tekrar başvuru beklemesi
    db.commit()
    applicant = db.get(User, profile.user_id)
    if applicant is not None:
        key = "application_approved" if decision == "approve" else "application_rejected"
        send_push(
            applicant,
            msg(f"push_{key}_title", applicant.language),
            msg(f"push_{key}_body", applicant.language),
            data={"route": "profile"},
        )
    return {"id": profile.id, "status": profile.status}
