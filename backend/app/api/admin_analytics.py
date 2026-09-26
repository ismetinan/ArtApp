"""Admin analitiği (2026-09): uygulama içinden kullanım görünürlüğü.

Kapsam: aktiflik (DAU/WAU/MAU), huni, kohort retention, ders bazlı takılma,
ekonomi ve ANONİM kullanıcı listesi. Gizlilik ilkesi: yanıtlarda e-posta,
görünen ad ya da çizim içeriği YOK — kullanıcılar yalnız "#id" ile görünür.

Admin ve demo (App Review) hesapları sayımlara katılmaz; yoksa bir avuç
kullanıcılı erken dönemde kendi testlerimiz metrikleri boğar.

Veri kaynakları: çoğu metrik zaten var olan tablolardan türetilir
(UserProgress, Submission, AnalysisJob, JetonTransaction, Purchase).
Yeni olanlar: UserActivityDay (aktiflik) ve AppEvent (istemci olayları).
Hacim küçük olduğu için bazı birleştirmeler Python'da yapılıyor — SQLite
(test) ve Postgres (prod) arasında taşınabilir kalsın diye. Binlerce aktif
kullanıcıya çıkıldığında SQL'e taşınmalı.
"""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tables import (
    AnalysisJob,
    AppEvent,
    Assignment,
    JetonTransaction,
    Purchase,
    SkillNode,
    Submission,
    User,
    UserActivityDay,
    UserProgress,
)
from .mentors import require_admin

router = APIRouter(prefix="/admin/analytics", tags=["admin"])

# Demo/App Review hesapları (scripts/seed_demo.py) bu alan adını kullanır
INTERNAL_EMAIL_SUFFIX = "@artora.app"


def _utc(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:  # sqlite naive döner
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _real_user_filter():
    return and_(
        User.is_admin.is_(False),
        or_(User.email.is_(None), ~User.email.like(f"%{INTERNAL_EMAIL_SUFFIX}")),
    )


def _real_ids():
    return select(User.id).where(_real_user_filter())


def _count(db: Session, stmt) -> int:
    return db.execute(stmt).scalar_one() or 0


def _distinct_users(db: Session, column, *where) -> set[int]:
    return set(db.execute(select(column).where(*where).distinct()).scalars())


# ---------------------------------------------------------------- overview


@router.get("/overview")
def overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    today = _today()
    real = _real_ids()
    now = datetime.now(timezone.utc)

    def active_since(days: int) -> int:
        return _count(
            db,
            select(func.count(func.distinct(UserActivityDay.user_id))).where(
                UserActivityDay.day > today - timedelta(days=days),
                UserActivityDay.user_id.in_(real),
            ),
        )

    dau, wau, mau = active_since(1), active_since(7), active_since(30)

    users = db.execute(
        select(User.created_at, User.is_guest, User.platform, User.premium_until).where(
            _real_user_filter()
        )
    ).all()
    total = len(users)
    registered = sum(1 for u in users if not u.is_guest)
    premium = sum(1 for u in users if (_utc(u.premium_until) or now) > now)
    platforms = Counter((u.platform or "unknown") for u in users)

    start = today - timedelta(days=29)
    signups = Counter(
        _utc(u.created_at).date() for u in users if _utc(u.created_at).date() >= start
    )
    dau_rows = dict(
        db.execute(
            select(UserActivityDay.day, func.count(func.distinct(UserActivityDay.user_id)))
            .where(UserActivityDay.day >= start, UserActivityDay.user_id.in_(real))
            .group_by(UserActivityDay.day)
        ).all()
    )
    series = []
    for i in range(30):
        d = start + timedelta(days=i)
        series.append(
            {"day": d.isoformat(), "signups": signups.get(d, 0), "active": dau_rows.get(d, 0)}
        )

    return {
        "users_total": total,
        "users_registered": registered,
        "users_guest": total - registered,
        "guest_to_registered_rate": round(registered / total, 3) if total else 0,
        "premium_active": premium,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "stickiness": round(dau / mau, 3) if mau else 0,
        "new_users_7d": sum(
            1 for u in users if _utc(u.created_at).date() > today - timedelta(days=7)
        ),
        "platforms": dict(platforms),
        "series_30d": series,
    }


# ------------------------------------------------------------------ funnel


@router.get("/funnel")
def funnel(
    days: int | None = Query(default=None, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Kayıt → onboarding → ders → ödev → tamamlama → geri dönüş.
    days verilirse yalnız son N günde kayıt olan kohort."""
    where = [_real_user_filter()]
    if days is not None:
        where.append(User.created_at >= datetime.now(timezone.utc) - timedelta(days=days))
    cohort = {
        row.id: row
        for row in db.execute(select(User.id, User.created_at, User.is_guest).where(*where))
    }
    ids = set(cohort)

    onboarded = _distinct_users(db, Submission.user_id, Submission.kind == "onboarding")
    opened = _distinct_users(db, AppEvent.user_id, AppEvent.name == "lesson_opened")
    generated = _distinct_users(db, Assignment.user_id)
    submitted = _distinct_users(db, Submission.user_id, Submission.kind == "assignment")
    completed = _distinct_users(db, UserProgress.user_id)
    last_active = dict(
        db.execute(
            select(UserActivityDay.user_id, func.max(UserActivityDay.day)).group_by(
                UserActivityDay.user_id
            )
        ).all()
    )
    returned = {
        uid
        for uid, row in cohort.items()
        if uid in last_active
        and last_active[uid] >= _utc(row.created_at).date() + timedelta(days=7)
    }

    steps = [
        ("signed_up", ids),
        ("onboarded", ids & onboarded),
        ("lesson_opened", ids & opened),
        ("assignment_generated", ids & generated),
        ("assignment_submitted", ids & submitted),
        ("lesson_completed", ids & completed),
        ("returned_after_7d", returned),
        ("registered_account", {u for u, r in cohort.items() if not r.is_guest}),
    ]
    base = len(ids) or 1
    return {
        "cohort_size": len(ids),
        "steps": [
            {"key": k, "users": len(v), "rate": round(len(v) / base, 3)} for k, v in steps
        ],
        # lesson_opened istemci olayıdır; 0.10 sürümünden önce toplanmıyordu
        "notes": ["lesson_opened_tracked_since_v0.10"],
    }


# --------------------------------------------------------------- retention

# (etiket, pencere başı, pencere sonu) — kayıttan sonraki gün aralığı, dahil
_RETENTION_WINDOWS = (("w1", 1, 7), ("w2", 8, 14), ("w4", 22, 28))


@router.get("/retention")
def retention(
    weeks: int = Query(default=8, ge=1, le=26),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Haftalık kayıt kohortları: kayıttan sonraki 1., 2. ve 4. haftada en az bir
    gün aktif olanların oranı. Henüz o haftaya ulaşmamış kohortta değer null."""
    today = _today()
    this_monday = today - timedelta(days=today.weekday())
    first_monday = this_monday - timedelta(weeks=weeks - 1)

    users = db.execute(
        select(User.id, User.created_at).where(
            _real_user_filter(),
            User.created_at >= datetime.combine(first_monday, datetime.min.time(), timezone.utc),
        )
    ).all()
    created = {u.id: _utc(u.created_at).date() for u in users}
    days_by_user: dict[int, set[date]] = defaultdict(set)
    if created:
        for uid, d in db.execute(
            select(UserActivityDay.user_id, UserActivityDay.day).where(
                UserActivityDay.user_id.in_(list(created))
            )
        ):
            days_by_user[uid].add(d)

    cohorts = []
    for w in range(weeks):
        start = first_monday + timedelta(weeks=w)
        members = [u for u, c in created.items() if start <= c < start + timedelta(weeks=1)]
        row = {"week_start": start.isoformat(), "size": len(members)}
        for label, lo, hi in _RETENTION_WINDOWS:
            # Kohortun EN GENÇ üyesi pencerenin sonuna ulaşmadıysa ölçüm eksik
            if start + timedelta(days=6 + hi) > today:
                row[label] = None
                continue
            kept = sum(
                1
                for u in members
                if any(
                    created[u] + timedelta(days=lo) <= d <= created[u] + timedelta(days=hi)
                    for d in days_by_user.get(u, ())
                )
            )
            row[label] = round(kept / len(members), 3) if members else None
        cohorts.append(row)
    return {"cohorts": cohorts}


# ----------------------------------------------------------------- lessons


@router.get("/lessons")
def lessons(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Ders bazlı takılma analizi: kaç kişi açtı, ödev üretti, gönderdi, geçti."""
    real = _real_ids()
    nodes = db.execute(select(SkillNode.id, SkillNode.title, SkillNode.skill_axis)).all()

    def per_node_users(column_node, column_user, *where) -> dict[str, int]:
        return dict(
            db.execute(
                select(column_node, func.count(func.distinct(column_user)))
                .where(column_user.in_(real), *where)
                .group_by(column_node)
            ).all()
        )

    generated = per_node_users(Assignment.node_id, Assignment.user_id)
    submitters = per_node_users(
        Submission.node_id, Submission.user_id, Submission.kind == "assignment"
    )
    completions = per_node_users(UserProgress.node_id, UserProgress.user_id)

    opened: dict[str, set[int]] = defaultdict(set)
    for uid, props in db.execute(
        select(AppEvent.user_id, AppEvent.props).where(
            AppEvent.name == "lesson_opened", AppEvent.user_id.in_(real)
        )
    ):
        node_id = (props or {}).get("node_id")
        if node_id:
            opened[node_id].add(uid)

    # Ödev uyumu (Faz C): analizde task_match varsa ortalaması
    matches: dict[str, list[int]] = defaultdict(list)
    for node_id, result in db.execute(
        select(Submission.node_id, Submission.ai_result).where(
            Submission.kind == "assignment",
            Submission.node_id.is_not(None),
            Submission.user_id.in_(real),
        )
    ):
        tm = (result or {}).get("task_match")
        if isinstance(tm, int):
            matches[node_id].append(tm)

    rows = []
    for n in nodes:
        sub = submitters.get(n.id, 0)
        done = completions.get(n.id, 0)
        m = matches.get(n.id)
        rows.append(
            {
                "node_id": n.id,
                "title": n.title,
                "axis": n.skill_axis,
                "opened": len(opened.get(n.id, ())),
                "assignment_generated": generated.get(n.id, 0),
                "submitters": sub,
                "completed": done,
                # Gönderip geçemeyenler: ödev uyumu eşiği (Faz C) sonrası anlamlı
                "stuck": max(sub - done, 0),
                "avg_task_match": round(sum(m) / len(m)) if m else None,
            }
        )
    rows.sort(key=lambda r: (-r["opened"], -r["submitters"], r["node_id"]))
    return {"lessons": rows}


# ----------------------------------------------------------------- economy


@router.get("/economy")
def economy(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    real = _real_ids()
    since = datetime.now(timezone.utc) - timedelta(days=30)

    spent = dict(
        db.execute(
            select(JetonTransaction.reason, func.sum(-JetonTransaction.delta))
            .where(JetonTransaction.delta < 0, JetonTransaction.user_id.in_(real))
            .group_by(JetonTransaction.reason)
        ).all()
    )
    granted = dict(
        db.execute(
            select(JetonTransaction.reason, func.sum(JetonTransaction.delta))
            .where(JetonTransaction.delta > 0, JetonTransaction.user_id.in_(real))
            .group_by(JetonTransaction.reason)
        ).all()
    )
    purchases = dict(
        db.execute(
            select(Purchase.product_id, func.count())
            .where(Purchase.user_id.in_(real))
            .group_by(Purchase.product_id)
        ).all()
    )

    jobs = db.execute(
        select(AnalysisJob.status, AnalysisJob.created_at, AnalysisJob.finished_at).where(
            AnalysisJob.created_at >= since, AnalysisJob.user_id.in_(real)
        )
    ).all()
    by_status = Counter(j.status for j in jobs)
    durations = [
        (_utc(j.finished_at) - _utc(j.created_at)).total_seconds()
        for j in jobs
        if j.status == "done" and j.finished_at is not None
    ]
    finished = by_status.get("done", 0) + by_status.get("failed", 0)

    return {
        "jetons_spent_by_reason": {k: int(v) for k, v in spent.items()},
        "jetons_granted_by_reason": {k: int(v) for k, v in granted.items()},
        "purchases_by_product": purchases,
        "ai_jobs_30d": {
            "by_status": dict(by_status),
            "fail_rate": round(by_status.get("failed", 0) / finished, 3) if finished else 0,
            "avg_seconds": round(sum(durations) / len(durations), 1) if durations else None,
        },
    }


# ------------------------------------------------------------------- users

_SORTS = {"last_seen", "created", "lessons", "analyses", "level"}
PAGE_SIZE = 50


@router.get("/users")
def users(
    sort: str = Query(default="last_seen"),
    page: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """ANONİM kullanıcı listesi: e-posta/ad yok, yalnız sayılar."""
    if sort not in _SORTS:
        sort = "last_seen"
    lessons_sq = (
        select(UserProgress.user_id, func.count().label("n"))
        .group_by(UserProgress.user_id)
        .subquery()
    )
    analyses_sq = (
        select(Submission.user_id, func.count().label("n"))
        .where(Submission.kind.in_(("assignment", "free")))
        .group_by(Submission.user_id)
        .subquery()
    )
    days_sq = (
        select(UserActivityDay.user_id, func.count().label("n"))
        .group_by(UserActivityDay.user_id)
        .subquery()
    )
    lessons_n = func.coalesce(lessons_sq.c.n, 0)
    analyses_n = func.coalesce(analyses_sq.c.n, 0)
    order = {
        "last_seen": User.last_seen_at.desc().nulls_last(),
        "created": User.created_at.desc(),
        "lessons": lessons_n.desc(),
        "analyses": analyses_n.desc(),
        "level": User.level.desc(),
    }[sort]

    stmt = (
        select(
            User.id,
            User.created_at,
            User.last_seen_at,
            User.platform,
            User.app_version,
            User.level,
            User.is_guest,
            User.premium_until,
            lessons_n.label("lessons"),
            analyses_n.label("analyses"),
            func.coalesce(days_sq.c.n, 0).label("active_days"),
        )
        .outerjoin(lessons_sq, lessons_sq.c.user_id == User.id)
        .outerjoin(analyses_sq, analyses_sq.c.user_id == User.id)
        .outerjoin(days_sq, days_sq.c.user_id == User.id)
        .where(_real_user_filter())
        .order_by(order, User.id.desc())
        .limit(PAGE_SIZE)
        .offset(page * PAGE_SIZE)
    )
    now = datetime.now(timezone.utc)
    total = _count(db, select(func.count()).select_from(User).where(_real_user_filter()))
    return {
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "users": [
            {
                "id": r.id,
                "created_at": _utc(r.created_at).isoformat(),
                "last_seen_at": _utc(r.last_seen_at).isoformat() if r.last_seen_at else None,
                "platform": r.platform,
                "app_version": r.app_version,
                "level": r.level,
                "is_guest": r.is_guest,
                "is_premium": (_utc(r.premium_until) or now) > now,
                "lessons_completed": r.lessons,
                "analyses": r.analyses,
                "active_days": r.active_days,
            }
            for r in db.execute(stmt)
        ],
    }
