"""Mentor kazanç defteri (Faz 4 — gelir paylaşımı, Faz A: ödemesiz biriktirme).

Mentor bir isteği cevapladığında (answered — terminal, iadesi yok) kazancı öğrencinin
harcadığı jeton_cost kadar JETON-EŞDEĞERİ olarak deftere işlenir. Para çevrimi +
paylaşım oranı Faz B'de payout anında uygulanır. request_id unique olduğundan aynı
istek iki kez kredi veremez. commit çağıranın sorumluluğunda (cevap + kredi tek
transaction'da kalsın diye — jetons.py deseniyle aynı).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.tables import MentorEarning, MentorshipRequest


def credit(db: Session, mentor_id: int, request: MentorshipRequest) -> None:
    """Cevaplanan istek için mentora jeton-eşdeğeri kazanç işler.
    request_id zaten deftere girmişse sessizce atlar (idempotent)."""
    exists = db.execute(
        select(MentorEarning.id).where(MentorEarning.request_id == request.id)
    ).scalar_one_or_none()
    if exists is not None:
        return
    db.add(
        MentorEarning(
            mentor_id=mentor_id,
            request_id=request.id,
            jeton_equivalent=request.jeton_cost,
            reason="mentor_feedback",
        )
    )


def summary(db: Session, mentor_id: int) -> dict:
    """mentor_id → {jeton_equivalent: toplam kazanç, answered_count: kayıt sayısı}."""
    total, count = db.execute(
        select(
            func.coalesce(func.sum(MentorEarning.jeton_equivalent), 0),
            func.count(MentorEarning.id),
        ).where(MentorEarning.mentor_id == mentor_id)
    ).one()
    return {"jeton_equivalent": int(total), "answered_count": int(count)}
