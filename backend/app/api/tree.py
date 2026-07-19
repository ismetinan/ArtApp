import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import get_ai_provider, guard_redline
from ..api.deps import get_current_user
from ..core.config import get_settings
from ..core.messages import msg
from ..db import get_db
from ..models.tables import (
    AbilityScore,
    Assignment,
    SkillNode,
    Submission,
    User,
    UserProgress,
)
from ..services.billing import is_premium
from ..services.gamification import award_xp, bump_ability
from ..services.quota import consume_ai_quota
from ..services.storage import UploadError, save_drawing

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

    consume_ai_quota(db, user)
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
    consume_ai_quota(db, user)

    content = await file.read()
    try:
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


# ---------- Serbest çizim analizi ----------

FREE_ANALYSIS_WINDOW = timedelta(days=7)
_FREE_CONTEXT = {"tr": "serbest çalışma", "en": "free study"}


@router.post("/free-analysis")
async def free_analysis(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ders dışı bitmiş bir çizimin analizi. Ücretsiz katman: haftada 1;
    Premium: yalnız günlük AI kotası sınırlar (müşteri isteği, 2026-07-19)."""
    if not is_premium(user):
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
    consume_ai_quota(db, user)

    content = await file.read()
    try:
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
