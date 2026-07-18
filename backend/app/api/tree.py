import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import get_ai_provider, guard_redline
from ..api.deps import get_current_user
from ..core.messages import msg
from ..db import get_db
from ..models.tables import SkillNode, Submission, User, UserProgress
from ..services.gamification import award_xp, bump_ability
from ..services.quota import consume_ai_quota
from ..services.storage import UploadError, save_drawing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skill-tree", tags=["skill-tree"])


def _completed_ids(db: Session, user: User) -> set[str]:
    rows = db.execute(select(UserProgress.node_id).where(UserProgress.user_id == user.id))
    return {r[0] for r in rows}


def _node_status(node: SkillNode, completed: set[str]) -> str:
    if node.id in completed:
        return "completed"
    if all(p in completed for p in node.prerequisites):
        return "available"
    return "locked"


def _node_title(node: SkillNode, lang: str) -> str:
    return node.title_en if lang == "en" and node.title_en else node.title


def _node_description(node: SkillNode, lang: str) -> str:
    return node.description_en if lang == "en" and node.description_en else node.description


@router.get("")
def get_tree(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    completed = _completed_ids(db, user)
    nodes = db.execute(select(SkillNode)).scalars().all()
    return {
        "nodes": [
            {
                "id": n.id,
                "title": _node_title(n, user.language),
                "description": _node_description(n, user.language),
                "youtube_video_id": n.youtube_video_id,
                "skill_axis": n.skill_axis,
                "xp_reward": n.xp_reward,
                "prerequisites": n.prerequisites,
                "resources": n.resources,
                "status": _node_status(n, completed),
            }
            for n in nodes
        ]
    }


@router.post("/{node_id}/submit")
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
    if _node_status(node, completed) == "locked":
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
