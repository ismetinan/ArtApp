"""Mentor defteri.

Mentor bir isteği cevapladığında (answered — terminal, iadesi yok) bir satır
işlenir. request_id unique olduğundan aynı istek iki kez kredi veremez. commit
çağıranın sorumluluğunda (cevap + kredi tek transaction'da kalsın diye —
jetons.py deseniyle aynı).

2026-08-08 kararıyla defter PARA defteri değil İTİBAR defteri: mentorluk
ücretsiz, mentora ödeme yalnız uygulama dışı isteğe bağlı bağışla oluyor ve
Artora para akışına hiç girmiyor. Dolayısıyla `paid_equivalent` (nakde
çevrilebilir kısım) yeni ekonomide daima 0 ve hiçbir nakit yükümlülüğü
doğurmuyor. Sütunlar geçmiş kayıtlar ve eski ekonomi yolu için korunuyor.
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
            paid_equivalent=request.paid_cost,  # gelir-destekli kısım (nakde çevrilebilir)
            reason="mentor_feedback",
        )
    )


def summary(db: Session, mentor_id: int) -> dict:
    """mentor_id → defter özeti.

    answered_count: cevaplanan istek sayısı — yeni ekonomide mentorun asıl
    göstergesi bu (itibar). jeton_equivalent/paid_equivalent eski ekonomi
    kayıtları için korunuyor; yeni kayıtlarda ikisi de 0."""
    total, paid, count = db.execute(
        select(
            func.coalesce(func.sum(MentorEarning.jeton_equivalent), 0),
            func.coalesce(func.sum(MentorEarning.paid_equivalent), 0),
            func.count(MentorEarning.id),
        ).where(MentorEarning.mentor_id == mentor_id)
    ).one()
    return {
        "jeton_equivalent": int(total),
        "paid_equivalent": int(paid),
        "answered_count": int(count),
    }
