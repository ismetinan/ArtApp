"""Asenkron AI analiz işleri (Faz 2, 2026-08-08).

Senkron akışta AI çağrısı istek içinde koşuyordu; commit en sonda olduğu için
AI patlarsa jeton harcaması da geri sarılıyordu — iade "bedava" geliyordu.
Asenkronda bu güvence KAYBOLUYOR: yükleme kendi transaction'ında commit ediliyor
ve jeton o anda düşüyor. Bu yüzden başarısız işte AÇIK İADE yapmak zorundayız
(para/güven akışı, CLAUDE.md §6). `refunded` bayrağı çift iadeyi engelliyor.

Çalıştırıcı: FastAPI BackgroundTasks — yanıt gönderildikten sonra aynı süreçte
koşar. Bu ölçekte yeterli; Celery/Redis ancak çok instance'a çıkınca gerekir.
Tek gerçek risk süreç yeniden başlarken koşan işin ortada kalması; onu tembel
zaman aşımı (`fail_stale`) yakalayıp iade ediyor — mentor isteklerindeki
`_expire_stale` deseninin aynısı.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import db as db_module  # modül üzerinden: testler engine'i yeniden bağlıyor
from ..core.messages import msg
from ..models.tables import AnalysisJob, User
from . import jetons
from .push import send_push

log = logging.getLogger(__name__)

# Bir iş bu süreden uzun "running"/"queued" kaldıysa süreç ölmüş sayılır.
# AI çağrısının kendi timeout'u 90 sn (ai/openrouter.py); pay bırakıyoruz.
STALE_AFTER = timedelta(minutes=10)


def create(
    db: Session,
    user: User,
    kind: str,
    submission_id: int,
    jeton_cost: int,
    node_id: str | None = None,
) -> AnalysisJob:
    """İşi kuyruğa alır. Çağıran commit eder (yükleme ile aynı transaction'da
    kalsın diye — iş satırı olmadan jeton harcanmış olmamalı)."""
    job = AnalysisJob(
        user_id=user.id,
        kind=kind,
        node_id=node_id,
        submission_id=submission_id,
        status="queued",
        jeton_cost=jeton_cost,
    )
    db.add(job)
    db.flush()  # job.id çağırana lazım
    return job


def _refund_if_needed(db: Session, job: AnalysisJob) -> None:
    """Başarısız işin jetonunu iade eder. İdempotent: `refunded` bayrağı ikinci
    iadeyi engeller (aynı işi hem fail_stale hem de runner düşürebilir)."""
    if job.refunded or job.jeton_cost <= 0:
        return
    user = db.get(User, job.user_id)
    if user is None:
        return
    jetons.grant(db, user, job.jeton_cost, "ai_refund")
    job.refunded = True


def mark_failed(db: Session, job: AnalysisJob, error_code: str) -> None:
    job.status = "failed"
    job.error_code = error_code
    job.finished_at = datetime.now(timezone.utc)
    _refund_if_needed(db, job)


def fail_stale(db: Session, user_id: int) -> bool:
    """Kullanıcının takılı kalmış işlerini düşürür + iade eder.

    Tembel tetikleme: iş listesi/sorgusu her okunduğunda çalışır. Süreç yeniden
    başladığında "running" kalan işler böyle temizleniyor — ayrı bir zamanlayıcı
    kurmadan. Değişiklik olduysa True döner (çağıran commit'ler)."""
    cutoff = datetime.now(timezone.utc) - STALE_AFTER
    jobs = db.execute(
        select(AnalysisJob).where(
            AnalysisJob.user_id == user_id,
            AnalysisJob.status.in_(("queued", "running")),
        )
    ).scalars().all()
    changed = False
    for job in jobs:
        created = job.created_at
        if created is not None and created.tzinfo is None:  # sqlite naive
            created = created.replace(tzinfo=timezone.utc)
        if created is not None and created < cutoff:
            mark_failed(db, job, "ai_unavailable")
            changed = True
    return changed


def to_json(job: AnalysisJob, lang: str) -> dict:
    """İstemcinin gördüğü hâli. Hata YERELLEŞTİRİLMİŞ metin olarak döner —
    istemcinin hata anahtarı sözlüğü tutmasına gerek kalmasın."""
    return {
        "job_id": job.id,
        "status": job.status,
        "kind": job.kind,
        "node_id": job.node_id,
        "submission_id": job.submission_id,
        "analysis": job.result,
        "xp_awarded": job.xp_awarded,
        "error": msg(job.error_code, lang) if job.error_code else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


async def run(job_id: int, image: bytes, node_title: str | None, language: str) -> None:
    """Arka plan işi: AI'ı çağırır, sonucu işler, kullanıcıya push atar.

    KENDİ oturumunu açar — isteğin oturumu yanıt gönderilirken kapanıyor.
    Hiçbir istisnayı dışarı sızdırmaz: BackgroundTasks içinde patlayan bir
    exception sessizce kaybolur ve iş sonsuza dek 'running' kalırdı.
    """
    # Geç import: modül yüklenirken ai paketini çekmeyelim (test monkeypatch'i
    # ai.factory üzerinden çalışıyor)
    from ..ai import get_ai_provider, guard_redline
    from ..models.tables import Submission, SkillNode, UserProgress
    from .billing import is_premium
    from .gamification import award_xp, bump_ability

    with db_module.SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        if job is None or job.status != "queued":
            return
        job.status = "running"
        db.commit()

        # Premium = güçlü model (Aşama 1). Kullanıcı işin sahibi.
        owner = db.get(User, job.user_id)
        premium = owner is not None and is_premium(owner)
        try:
            result = guard_redline(
                await get_ai_provider(premium=premium).redline_analysis(
                    image, node_title or "", language=language
                ),
                language=language,
            )
        except Exception:
            log.exception("AI analizi başarısız (job=%s)", job_id)
            job = db.get(AnalysisJob, job_id)
            if job is not None:
                mark_failed(db, job, "ai_unavailable")
                db.commit()
                _notify(db, job, ok=False)
            return

        job = db.get(AnalysisJob, job_id)
        if job is None:
            return
        payload = result.model_dump(mode="json")
        job.result = payload
        job.status = "done"
        job.finished_at = datetime.now(timezone.utc)

        submission = db.get(Submission, job.submission_id) if job.submission_id else None
        if submission is not None:
            submission.ai_result = payload

        user = db.get(User, job.user_id)
        # İlerleme yalnız ders ödevinde işlenir (serbest analiz XP vermez)
        if job.kind == "assignment" and job.node_id and user is not None:
            node = db.get(SkillNode, job.node_id)
            already = db.execute(
                select(UserProgress.id).where(
                    UserProgress.user_id == user.id, UserProgress.node_id == job.node_id
                )
            ).first()
            if node is not None and already is None:
                db.add(
                    UserProgress(
                        user_id=user.id, node_id=node.id, xp_earned=node.xp_reward
                    )
                )
                award_xp(user, node.xp_reward)
                job.xp_awarded = node.xp_reward
            # Chart her analizde güncellenir — tekrar pratikte de (Faz 3)
            if node is not None:
                bump_ability(db, user, node.skill_axis, findings=payload.get("findings"))
        elif job.kind == "free" and user is not None:
            bump_ability(db, user, None, findings=payload.get("findings"))

        db.commit()
        _notify(db, job, ok=True)


def _notify(db: Session, job: AnalysisJob, ok: bool) -> None:
    """Analiz bitince push — kullanıcı uygulamadan çıkmış olabilir, asıl mesele
    bu (senkron akışta çıkarsa sonucu hiç göremiyordu)."""
    user = db.get(User, job.user_id)
    if user is None:
        return
    key = "push_analysis_ready" if ok else "push_analysis_failed"
    send_push(
        user,
        msg(f"{key}_title", user.language),
        msg(f"{key}_body", user.language),
        data={"route": "analysis_job", "job_id": str(job.id)},
    )
