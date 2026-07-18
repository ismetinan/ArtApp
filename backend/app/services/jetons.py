"""Jeton ekonomisi (Faz 2, ödemesiz beta).

Her bakiye değişimi bir JetonTransaction satırıyla belgelenir; bakiye hiçbir
yolda negatife düşemez (para/güven akışı — CLAUDE.md §6). Satın alma yok:
tek gelir hoşgeldin jetonu (WELCOME_JETONS), tek gider mentor isteği.
commit çağıranın sorumluluğunda — harcama + istek oluşturma tek transaction'da
kalsın diye.
"""

from fastapi import HTTPException

from sqlalchemy.orm import Session

from ..core.messages import msg
from ..models.tables import JetonTransaction, MentorshipRequest, User

WELCOME_JETONS = 3


def grant(db: Session, user: User, amount: int, reason: str) -> None:
    if amount <= 0:
        raise ValueError("grant miktarı pozitif olmalı")
    user.jeton_balance += amount
    db.add(JetonTransaction(user_id=user.id, delta=amount, reason=reason))


def grant_welcome(db: Session, user: User) -> None:
    grant(db, user, WELCOME_JETONS, "welcome")


def spend(db: Session, user: User, amount: int, request: MentorshipRequest) -> None:
    """Bakiye düşer; yetersizse yerelleştirilmiş 402 (hiçbir şey değişmez)."""
    if amount <= 0:
        raise ValueError("spend miktarı pozitif olmalı")
    if user.jeton_balance < amount:
        raise HTTPException(
            status_code=402, detail=msg("jeton_insufficient", user.language, cost=amount)
        )
    user.jeton_balance -= amount
    db.add(
        JetonTransaction(
            user_id=user.id, delta=-amount, reason="mentor_request", request_id=request.id
        )
    )


def refund(db: Session, student: User, request: MentorshipRequest) -> None:
    """Zaman aşımına uğrayan isteğin jetonunu iade eder (idempotent değil —
    çağıran, isteği expired'a çevirdiği tek noktada kullanmalı)."""
    student.jeton_balance += request.jeton_cost
    db.add(
        JetonTransaction(
            user_id=student.id,
            delta=request.jeton_cost,
            reason="refund",
            request_id=request.id,
        )
    )
