"""XP / seviye / eksen skoru mantığı — tek yerde ki dengeleme kolay olsun."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.tables import AbilityScore, User

XP_PER_LEVEL = 100
AXIS_BUMP_PER_NODE = 8  # bir ders tamamlamanın ilgili eksene katkısı


def level_for_xp(xp: int) -> int:
    return 1 + xp // XP_PER_LEVEL


def award_xp(user: User, amount: int) -> None:
    user.xp += amount
    user.level = level_for_xp(user.xp)


def bump_ability(db: Session, user: User, axis: str, amount: int = AXIS_BUMP_PER_NODE) -> None:
    score = db.execute(
        select(AbilityScore).where(AbilityScore.user_id == user.id, AbilityScore.axis == axis)
    ).scalar_one_or_none()
    if score is None:
        score = AbilityScore(user_id=user.id, axis=axis, score=0)
        db.add(score)
    score.score = min(100, score.score + amount)
