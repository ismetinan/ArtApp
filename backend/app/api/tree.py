import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import get_ai_provider, guard_redline
from ..api.deps import get_current_user
from ..core.config import get_settings
from ..core.messages import msg
from ..db import get_db
from ..models.tables import (
    AbilityScore,
    AnalysisJob,
    Assignment,
    SkillNode,
    Submission,
    User,
    UserProgress,
)
from ..services.billing import is_premium
from ..services.gamification import award_xp, bump_ability
from ..services import analysis_jobs
from ..services.quota import spend_ai
from ..services.storage import UploadError, read_upload, save_drawing

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skill-tree"])


def _completed_ids(db: Session, user: User) -> set[str]:
    rows = db.execute(select(UserProgress.node_id).where(UserProgress.user_id == user.id))
    return {r[0] for r in rows}


def _ability_scores(db: Session, user: User) -> dict[str, int]:
    rows = db.execute(select(AbilityScore).where(AbilityScore.user_id == user.id))
    return {s.axis: s.score for s in rows.scalars()}


def _prereq_satisfied(
    prereq: SkillNode | None, completed: set[str], scores: dict[str, int]
) -> bool:
    """Önkoşul tamamlandıysa VEYA öğrencinin o önkoşulun eksenindeki skoru
    eşiği geçiyorsa (skora göre atlama — müşteri isteği) sağlanmış sayılır."""
    if prereq is None:  # seed dışı referans — engelleme
        return True
    if prereq.id in completed:
        return True
    return scores.get(prereq.skill_axis, 0) >= get_settings().skip_unlock_score


def _node_status(
    node: SkillNode,
    completed: set[str],
    scores: dict[str, int],
    by_id: dict[str, SkillNode],
) -> tuple[str, bool]:
    """(status, unlocked_by_score) döndürür."""
    if node.id in completed:
        return "completed", False
    unmet = [p for p in node.prerequisites if p not in completed]
    if not unmet:
        return "available", False
    if all(_prereq_satisfied(by_id.get(p), completed, scores) for p in unmet):
        return "available", True
    return "locked", False


def _node_title(node: SkillNode, lang: str) -> str:
    return node.title_en if lang == "en" and node.title_en else node.title


def _node_description(node: SkillNode, lang: str) -> str:
    return node.description_en if lang == "en" and node.description_en else node.description


@router.get("/skill-tree")
def get_tree(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    completed = _completed_ids(db, user)
    scores = _ability_scores(db, user)
    nodes = db.execute(select(SkillNode)).scalars().all()
    by_id = {n.id: n for n in nodes}

    payload, available = [], []
    for n in nodes:
        status, by_score = _node_status(n, completed, scores, by_id)
        if status == "available":
            available.append(n)
        payload.append(
            {
                "id": n.id,
                "title": _node_title(n, user.language),
                "description": _node_description(n, user.language),
                "youtube_video_id": n.youtube_video_id,
                "skill_axis": n.skill_axis,
                "xp_reward": n.xp_reward,
                "prerequisites": n.prerequisites,
                "resources": n.resources,
                "status": status,
                "unlocked_by_score": by_score,
            }
        )

    # Tavsiye edilen ders: açık düğümler içinde ekseni en zayıf olan —
    # "yanlış yönde yıl kaybetme" vaadinin ağaçtaki karşılığı.
    recommended = min(
        available, key=lambda n: scores.get(n.skill_axis, 0), default=None
    )
    return {
        "nodes": payload,
        "recommended_node_id": recommended.id if recommended else None,
    }


# ---------- AI ödev üretimi ----------


def _assignment_row(db: Session, user: User, node_id: str) -> Assignment | None:
    return db.execute(
        select(Assignment).where(
            Assignment.user_id == user.id, Assignment.node_id == node_id
        )
    ).scalar_one_or_none()


@router.get("/skill-tree/{node_id}/assignment")
def get_assignment(
    node_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kayıtlı ödevi döndürür (kota harcamaz); yoksa null."""
    row = _assignment_row(db, user, node_id)
    return {"assignment": row.text if row else None}


@router.post("/skill-tree/{node_id}/assignment")
async def generate_assignment(
    node_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ödev görevini AI'a ürettirir; kişi+düğüm başına bir kez (sonrası önbellek)."""
    node = db.get(SkillNode, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=msg("node_not_found", user.language))
    row = _assignment_row(db, user, node_id)
    if row is not None:
        return {"assignment": row.text}

    # Ücretsiz (ai_cost_assignment=0): metin üretimi ucuz ve zaten önbellekli.
    spend_ai(db, user, get_settings().ai_cost_assignment, "ai_assignment")
    try:
        brief = await get_ai_provider().assignment_brief(
            _node_title(node, user.language),
            _node_description(node, user.language),
            language=user.language,
        )
    except Exception:
        logger.exception("AI ödev üretimi başarısız (node=%s)", node_id)
        raise HTTPException(status_code=503, detail=msg("ai_unavailable", user.language))
    db.add(Assignment(user_id=user.id, node_id=node_id, text=brief.assignment_tr))
    db.commit()
    return {"assignment": brief.assignment_tr}


# ---------- Ödev gönderimi (çekirdek döngü) ----------


@router.post("/skill-tree/{node_id}/submit")
async def submit_assignment(
    node_id: str,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Çekirdek döngü: ödev yükle → AI redline al → XP/ilerleme güncelle."""
    node = db.get(SkillNode, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=msg("node_not_found", user.language))

    completed = _completed_ids(db, user)
    scores = _ability_scores(db, user)
    nodes = db.execute(select(SkillNode)).scalars().all()
    by_id = {n.id: n for n in nodes}
    if _node_status(node, completed, scores, by_id)[0] == "locked":
        raise HTTPException(status_code=403, detail=msg("node_locked", user.language))
    # Çekirdek döngü: redline analizi jetonla (yeni ekonomide 1 jeton).
    spend_ai(db, user, get_settings().ai_cost_redline, "ai_redline")

    try:
        content = await read_upload(file)
        rel_path = save_drawing(content, file.filename or "odev.png")
    except UploadError as e:
        raise HTTPException(status_code=422, detail=msg(e.code, user.language, **e.params))

    try:
        result = guard_redline(
            await get_ai_provider().redline_analysis(
                content, _node_title(node, user.language), language=user.language
            ),
            language=user.language,
        )
    except Exception:
        logger.exception("AI redline analizi başarısız (node=%s)", node.id)
        raise HTTPException(status_code=503, detail=msg("ai_unavailable", user.language))

    submission = Submission(
        user_id=user.id,
        node_id=node.id,
        kind="assignment",
        file_path=rel_path,
        ai_result=result.model_dump(mode="json"),
    )
    db.add(submission)

    first_completion = node.id not in completed
    if first_completion:
        db.add(UserProgress(user_id=user.id, node_id=node.id, xp_earned=node.xp_reward))
        award_xp(user, node.xp_reward)
        bump_ability(db, user, node.skill_axis)
    db.commit()

    return {
        "submission_id": submission.id,
        "analysis": result,
        "xp_awarded": node.xp_reward if first_completion else 0,
        "level": user.level,
        "xp": user.xp,
    }


# ---------- Asenkron analiz (Faz 2) ----------
#
# Senkron uçlar YUKARIDA aynen duruyor: Play'deki eski sürümler onları çağırıyor
# ve kırılmamalı. Yeni istemci aşağıdaki -async uçlarını kullanır; fark, AI'ın
# yanıt içinde değil arka planda koşması ve istemcinin iş kimliğiyle sonucu
# istediği zaman alabilmesi (uygulama kapansa bile).


@router.post("/skill-tree/{node_id}/submit-async")
async def submit_assignment_async(
    node_id: str,
    background: BackgroundTasks,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ödevi yükler ve analiz işini kuyruğa alır; iş kimliğini hemen döner."""
    node = db.get(SkillNode, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=msg("node_not_found", user.language))

    completed = _completed_ids(db, user)
    scores = _ability_scores(db, user)
    nodes = db.execute(select(SkillNode)).scalars().all()
    by_id = {n.id: n for n in nodes}
    if _node_status(node, completed, scores, by_id)[0] == "locked":
        raise HTTPException(status_code=403, detail=msg("node_locked", user.language))

    # Takılı kalmış işleri önce düşür: hem iadeleri işler hem de aşağıdaki
    # "zaten çalışan iş var mı" kontrolü doğru sonuç versin.
    if analysis_jobs.fail_stale(db, user.id):
        db.commit()
    active = db.execute(
        select(AnalysisJob.id).where(
            AnalysisJob.user_id == user.id,
            AnalysisJob.status.in_(("queued", "running")),
        )
    ).first()
    if active is not None:
        raise HTTPException(
            status_code=409, detail=msg("analysis_in_progress", user.language)
        )

    try:
        content = await read_upload(file)
        rel_path = save_drawing(content, file.filename or "odev.png")
    except UploadError as e:
        raise HTTPException(status_code=422, detail=msg(e.code, user.language, **e.params))

    cost = get_settings().ai_cost_redline
    spend_ai(db, user, cost, "ai_redline")  # yetersizse 402, hiçbir şey yazılmaz
    submission = Submission(
        user_id=user.id, node_id=node.id, kind="assignment", file_path=rel_path
    )
    db.add(submission)
    db.flush()
    job = analysis_jobs.create(
        db, user, "assignment", submission.id, cost, node_id=node.id
    )
    db.commit()

    background.add_task(
        analysis_jobs.run, job.id, content, _node_title(node, user.language), user.language
    )
    return {"job_id": job.id, "submission_id": submission.id, "status": "queued"}


@router.post("/free-analysis-async")
async def free_analysis_async(
    background: BackgroundTasks,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Serbest çizim analizini kuyruğa alır; iş kimliğini hemen döner."""
    settings = get_settings()
    if analysis_jobs.fail_stale(db, user.id):
        db.commit()
    active = db.execute(
        select(AnalysisJob.id).where(
            AnalysisJob.user_id == user.id,
            AnalysisJob.status.in_(("queued", "running")),
        )
    ).first()
    if active is not None:
        raise HTTPException(
            status_code=409, detail=msg("analysis_in_progress", user.language)
        )

    if not settings.jeton_ai_economy_enabled and not is_premium(user):
        cutoff = datetime.now(timezone.utc) - FREE_ANALYSIS_WINDOW
        recent = db.execute(
            select(Submission.id).where(
                Submission.user_id == user.id,
                Submission.kind == "free",
                Submission.created_at >= cutoff,
            )
        ).first()
        if recent is not None:
            raise HTTPException(
                status_code=429, detail=msg("free_analysis_limit", user.language)
            )

    try:
        content = await read_upload(file)
        rel_path = save_drawing(content, file.filename or "serbest.png")
    except UploadError as e:
        raise HTTPException(status_code=422, detail=msg(e.code, user.language, **e.params))

    cost = settings.ai_cost_free_analysis
    spend_ai(db, user, cost, "ai_free_analysis")
    submission = Submission(user_id=user.id, kind="free", file_path=rel_path)
    db.add(submission)
    db.flush()
    job = analysis_jobs.create(db, user, "free", submission.id, cost)
    db.commit()

    background.add_task(
        analysis_jobs.run, job.id, content, _FREE_CONTEXT.get(user.language), user.language
    )
    return {"job_id": job.id, "submission_id": submission.id, "status": "queued"}


@router.get("/analysis-jobs/latest")
def latest_analysis_job(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Kurtarma ucu: uygulama açılışta bunu sorgular. Uygulama analiz sırasında
    kapandıysa sonucu burada bulur — yeniden yükleyip ikinci kez jeton harcamaz."""
    if analysis_jobs.fail_stale(db, user.id):
        db.commit()
    job = db.execute(
        select(AnalysisJob)
        .where(AnalysisJob.user_id == user.id)
        .order_by(AnalysisJob.id.desc())
    ).scalars().first()
    if job is None:
        return {"job": None}
    return {"job": analysis_jobs.to_json(job, user.language)}


@router.get("/analysis-jobs/{job_id}")
def get_analysis_job(
    job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if analysis_jobs.fail_stale(db, user.id):
        db.commit()
    job = db.get(AnalysisJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail=msg("job_not_found", user.language))
    return analysis_jobs.to_json(job, user.language)


# ---------- Serbest çizim analizi ----------

FREE_ANALYSIS_WINDOW = timedelta(days=7)
_FREE_CONTEXT = {"tr": "serbest çalışma", "en": "free study"}


@router.post("/free-analysis")
async def free_analysis(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ders dışı bitmiş bir çizimin analizi.

    ESKİ ekonomi: ücretsiz katman haftada 1, Premium'u yalnız günlük kota sınırlar.
    YENİ ekonomi: haftalık pencere KALDIRILIR — kıtlığı jeton tabanı zaten
    yaratıyor, iki ayrı kısıtı üst üste bindirmek kullanıcıya iki kez ceza olur."""
    settings = get_settings()
    if not settings.jeton_ai_economy_enabled and not is_premium(user):
        cutoff = datetime.now(timezone.utc) - FREE_ANALYSIS_WINDOW
        recent = db.execute(
            select(Submission.id).where(
                Submission.user_id == user.id,
                Submission.kind == "free",
                Submission.created_at >= cutoff,
            )
        ).first()
        if recent is not None:
            raise HTTPException(
                status_code=429, detail=msg("free_analysis_limit", user.language)
            )
    spend_ai(db, user, settings.ai_cost_free_analysis, "ai_free_analysis")

    try:
        content = await read_upload(file)
        rel_path = save_drawing(content, file.filename or "serbest.png")
    except UploadError as e:
        raise HTTPException(status_code=422, detail=msg(e.code, user.language, **e.params))

    try:
        result = guard_redline(
            await get_ai_provider().redline_analysis(
                content,
                _FREE_CONTEXT.get(user.language, _FREE_CONTEXT["tr"]),
                language=user.language,
            ),
            language=user.language,
        )
    except Exception:
        logger.exception("AI serbest analiz başarısız (user=%s)", user.id)
        raise HTTPException(status_code=503, detail=msg("ai_unavailable", user.language))

    submission = Submission(
        user_id=user.id,
        node_id=None,
        kind="free",
        file_path=rel_path,
        ai_result=result.model_dump(mode="json"),
    )
    db.add(submission)
    db.commit()

    return {
        "submission_id": submission.id,
        "analysis": result,
        "xp_awarded": 0,
        "level": user.level,
        "xp": user.xp,
    }
