"""Jeton ekonomisi (Faz 2, ödemesiz beta).

Her bakiye değişimi bir JetonTransaction satırıyla belgelenir; bakiye hiçbir
yolda negatife düşemez (para/güven akışı — CLAUDE.md §6). Satın alma yok:
tek gelir hoşgeldin jetonu (WELCOME_JETONS), tek gider mentor isteği.
commit çağıranın sorumluluğunda — harcama + istek oluşturma tek transaction'da
kalsın diye.
"""

from fastapi import HTTPException

from sqlalchemy import update
from sqlalchemy.orm import Session

from ..core.messages import msg
from ..models.tables import JetonTransaction, MentorshipRequest, User

WELCOME_JETONS = 3


def _adjust_balance(db: Session, user: User, delta: int, paid_delta: int = 0) -> bool:
    """Bakiyeyi DB seviyesinde atomik değiştirir (read-modify-write yarışı yok).
    Negatif delta'da 'bakiye yeterli' koşulu UPDATE'in içindedir — eşzamanlı iki
    harcama bakiyeyi asla negatife düşüremez. paid_delta, gelir-destekli
    (jeton_paid_balance) bileşenini aynı atomik UPDATE'te değiştirir. Başarısızsa
    False döner."""
    values = {"jeton_balance": User.jeton_balance + delta}
    if paid_delta:
        values["jeton_paid_balance"] = User.jeton_paid_balance + paid_delta
    stmt = update(User).where(User.id == user.id).values(**values)
    if delta < 0:
        stmt = stmt.where(User.jeton_balance >= -delta)
    changed = db.execute(stmt).rowcount == 1
    # sonraki okuma güncel değeri çeksin
    db.expire(user, ["jeton_balance", "jeton_paid_balance"])
    return changed


def grant(db: Session, user: User, amount: int, reason: str, paid: bool = False) -> None:
    """paid=True: jeton gerçek gelirle destekli (satın alma/Premium) — nakde
    çevrilebilir mentor kazancı yalnız bu jetonlardan doğar. paid=False: ücretsiz
    (hoşgeldin) — itibar kazandırır ama nakit yükümlülüğü yaratmaz."""
    if amount <= 0:
        raise ValueError("grant miktarı pozitif olmalı")
    _adjust_balance(db, user, amount, paid_delta=amount if paid else 0)
    db.add(JetonTransaction(user_id=user.id, delta=amount, reason=reason))


def grant_welcome(db: Session, user: User) -> None:
    grant(db, user, WELCOME_JETONS, "welcome")  # ücretsiz (paid=False)


def spend(db: Session, user: User, amount: int, request: MentorshipRequest) -> None:
    """Bakiye düşer; yetersizse yerelleştirilmiş 402 (hiçbir şey değişmez).

    Önce-ücretsiz kuralı: harcanan jetonların önce ücretsiz kısmı tükenir; kalanı
    gelir-destekli jetonlardan düşülür. Bu harcamanın gelir-destekli parçası
    (paid_spent) istekte saklanır ki iade bileşimi geri yükleyebilsin ve cevap
    verildiğinde mentor kazancının nakde çevrilebilir kısmına taşınabilsin.

    Not: tek-aktif-token (tek cihaz) modelinde bir kullanıcının eşzamanlı harcaması
    gerçekleşmez; paid_spent kullanıcı nesnesinin güncel değerlerinden hesaplanır,
    aşırı-harcama koruması ise tek atomik UPDATE'in koşuluyla korunur."""
    if amount <= 0:
        raise ValueError("spend miktarı pozitif olmalı")
    free_balance = user.jeton_balance - user.jeton_paid_balance
    paid_spent = max(0, amount - free_balance)
    paid_spent = min(paid_spent, user.jeton_paid_balance)  # savunmacı: negatife düşme
    if not _adjust_balance(db, user, -amount, paid_delta=-paid_spent):
        raise HTTPException(
            status_code=402, detail=msg("jeton_insufficient", user.language, cost=amount)
        )
    request.paid_cost = paid_spent
    db.add(
        JetonTransaction(
            user_id=user.id, delta=-amount, reason="mentor_request", request_id=request.id
        )
    )


def refund(db: Session, student: User, request: MentorshipRequest) -> None:
    """Zaman aşımına uğrayan isteğin jetonunu iade eder (idempotent değil —
    çağıran, isteği expired'a çevirdiği tek noktada kullanmalı). Harcamadaki
    gelir-destekli/ücretsiz bileşimi (request.paid_cost) aynen geri yükler."""
    _adjust_balance(db, student, request.jeton_cost, paid_delta=request.paid_cost)
    db.add(
        JetonTransaction(
            user_id=student.id,
            delta=request.jeton_cost,
            reason="refund",
            request_id=request.id,
        )
    )
