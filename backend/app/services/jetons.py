"""Jeton ekonomisi.

Her bakiye değişimi bir JetonTransaction satırıyla belgelenir; bakiye hiçbir
yolda negatife düşemez (para/güven akışı — CLAUDE.md §6). commit çağıranın
sorumluluğunda — harcama + istek oluşturma tek transaction'da kalsın diye.

İki model bir arada yaşıyor, ayıran bayrak `jeton_ai_economy_enabled`:

- ESKİ (bayrak kapalı): jeton = mentor parası. Ücretsiz/altın ayrımı
  seçmeli mentorun "yalnız altın" kuralı için var; haftalık damla EKLER.
- YENİ (bayrak açık): jeton = AI kullanım birimi, mentorluk ücretsiz.
  Ücretsiz jeton haftalık TABANA tamamlanır (birikmez); satın alınan jeton
  (jeton_paid_balance) hiçbir zaman sıfırlanmaz ve süresi dolmaz — bu,
  Kullanım Koşulları'nda verilen taahhüt (bkz. /terms).
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from sqlalchemy import update
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.messages import msg
from ..models.tables import JetonTransaction, MentorshipRequest, User

WELCOME_JETONS = 3
WEEKLY_FREE_INTERVAL = timedelta(days=7)  # ücretsiz damla aralığı


def _adjust_balance(db: Session, user: User, delta: int, paid_delta: int = 0) -> bool:
    """Bakiyeyi DB seviyesinde atomik değiştirir (read-modify-write yarışı yok).
    Negatif delta'da 'bakiye yeterli' koşulu UPDATE'in içindedir — eşzamanlı iki
    harcama bakiyeyi asla negatife düşüremez. paid_delta, gelir-destekli
    (jeton_paid_balance = 'altın') bileşenini aynı atomik UPDATE'te değiştirir;
    negatif paid_delta'da altın bakiyesi de guard'lanır (altın yetersizse UPDATE
    hiç uygulanmaz — seçmeli mentorun 'yalnız altın' kuralını korur). Başarısızsa
    False döner."""
    values = {"jeton_balance": User.jeton_balance + delta}
    if paid_delta:
        values["jeton_paid_balance"] = User.jeton_paid_balance + paid_delta
    stmt = update(User).where(User.id == user.id).values(**values)
    if delta < 0:
        stmt = stmt.where(User.jeton_balance >= -delta)
    if paid_delta < 0:
        stmt = stmt.where(User.jeton_paid_balance >= -paid_delta)
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
    # Haftalık damlanın sayacını kayıttan başlat: ilk ücretsiz damla 7 gün sonra.
    user.free_jeton_last_grant = datetime.now(timezone.utc)


def _weekly_window_open(user: User, now: datetime) -> bool:
    """Son haftalık dokunuştan ≥7 gün geçti mi (ya da hiç dokunulmadı mı)?
    naive gelen (SQLite) değerler UTC varsayılır."""
    last = user.free_jeton_last_grant
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return now - last >= WEEKLY_FREE_INTERVAL


def free_balance(user: User) -> int:
    """Ücretsiz (gelir-desteksiz) bakiye. Saklanmaz, türetilir."""
    return user.jeton_balance - user.jeton_paid_balance


def maybe_grant_weekly(db: Session, user: User) -> bool:
    """Haftalık ücretsiz jeton işini yapan tek giriş noktası — aktif ekonomiye
    göre dallanır. Bakiye değiştiyse True döner (çağıran commit'lemeli)."""
    if get_settings().jeton_ai_economy_enabled:
        return maybe_topup_weekly(db, user)
    return maybe_grant_weekly_free(db, user)


def maybe_topup_weekly(db: Session, user: User) -> bool:
    """YENİ ekonomi: ücretsiz bakiyeyi haftalık TABANA tamamlar.

    Taban altındaysa tabana çıkar, üstünde ya da eşitse hiç jeton verilmez —
    ücretsiz jeton birikmez (2026-08-08 kararı). Satın alınmış jetona
    (jeton_paid_balance) asla dokunulmaz: taban hesabı yalnız ücretsiz bileşeni
    baz alır, dolayısıyla satın alınan jeton ne silinir ne de tabanı doldurmuş
    sayılır. Tembel tetikleme — /profile açılışında çağrılır.

    Pencere kapalıysa hiçbir şey yapmaz (aynı hafta ikinci çağrı etkisiz)."""
    settings = get_settings()
    from .billing import is_premium  # döngüsel import kaçınma (bkz. quota.py)

    floor = (
        settings.weekly_jeton_floor_premium
        if is_premium(user)
        else settings.weekly_jeton_floor
    )
    if floor <= 0:
        return False
    now = datetime.now(timezone.utc)
    if not _weekly_window_open(user, now):
        return False
    missing = floor - free_balance(user)
    if missing <= 0:
        # Taban zaten dolu: jeton verilmez ama sayaç ilerler, yoksa her /profile
        # çağrısında yeniden hesaplanır. grant() amount<=0'da ValueError atar.
        user.free_jeton_last_grant = now
        return True
    grant(db, user, missing, "weekly_topup")  # ücretsiz (paid=False)
    user.free_jeton_last_grant = now
    return True


def maybe_grant_weekly_free(db: Session, user: User) -> bool:
    """ESKİ ekonomi: son ücretsiz damladan ≥7 gün geçtiyse bir kez ücretsiz jeton
    EKLER ve sayacı 'now' yapar. Damla verildiyse True döner (çağıran
    commit'lemeli). İdempotent: aynı hafta ikinci çağrı damlatmaz."""
    n = get_settings().weekly_free_jetons
    if n <= 0:
        return False
    now = datetime.now(timezone.utc)
    if not _weekly_window_open(user, now):
        return False
    grant(db, user, n, "weekly_free")  # ücretsiz (paid=False)
    user.free_jeton_last_grant = now
    return True


def spend(
    db: Session,
    user: User,
    amount: int,
    request: MentorshipRequest,
    gold_only: bool = False,
) -> None:
    """Bakiye düşer; yetersizse yerelleştirilmiş 402 (hiçbir şey değişmez).

    İki katman (CLAUDE.md §2, gelir paylaşımı):
    - gold_only=False (havuz): önce-ücretsiz kuralı — harcamanın önce ücretsiz kısmı
      tükenir, kalanı altından (gelir-destekli) düşülür.
    - gold_only=True (seçmeli mentor): harcamanın TAMAMI altından düşer; ücretsiz
      jeton seçmeli mentoru satın alamaz. Altın yetersizse 402 'gold_insufficient'.

    Harcamanın gelir-destekli parçası (paid_spent) istekte saklanır ki iade bileşimi
    geri yükleyebilsin ve cevap verildiğinde mentor kazancının nakde çevrilebilir
    kısmına taşınabilsin.

    Not: tek-aktif-token (tek cihaz) modelinde bir kullanıcının eşzamanlı harcaması
    gerçekleşmez; paid_spent kullanıcı nesnesinin güncel değerlerinden hesaplanır,
    aşırı-harcama koruması ise tek atomik UPDATE'in koşuluyla korunur."""
    if amount <= 0:
        raise ValueError("spend miktarı pozitif olmalı")
    if gold_only:
        paid_spent = amount  # tümü altından; _adjust_balance altın guard'ıyla korur
        err_key = "gold_insufficient"
    else:
        paid_spent = max(0, amount - free_balance(user))
        paid_spent = min(paid_spent, user.jeton_paid_balance)  # savunmacı
        err_key = "jeton_insufficient"
    if not _adjust_balance(db, user, -amount, paid_delta=-paid_spent):
        raise HTTPException(
            status_code=402, detail=msg(err_key, user.language, cost=amount)
        )
    request.paid_cost = paid_spent
    db.add(
        JetonTransaction(
            user_id=user.id, delta=-amount, reason="mentor_request", request_id=request.id
        )
    )


def spend_for_ai(db: Session, user: User, amount: int, reason: str) -> None:
    """YENİ ekonomi: bir AI aksiyonu için jeton düşer; yetersizse 402.

    Önce-ücretsiz kuralı (mentor harcamasıyla aynı): ücretsiz bakiye tükenmeden
    satın alınmış jetona dokunulmaz. Mentor isteğinden farkı, bağlanacak bir
    MentorshipRequest satırı olmaması — bu yüzden ayrı fonksiyon.

    commit ETMEZ. Çağıran, AI çağrısı başarılı olduktan sonra commit eder; AI
    patlarsa oturum commit'siz kapanır ve harcama geri sarılır (bkz. quota.py).
    Bu garanti önemli: başarısız AI çağrısı kullanıcıya jetona mal olmamalı."""
    if amount <= 0:
        raise ValueError("spend_for_ai miktarı pozitif olmalı")
    paid_spent = min(max(0, amount - free_balance(user)), user.jeton_paid_balance)
    if not _adjust_balance(db, user, -amount, paid_delta=-paid_spent):
        raise HTTPException(
            status_code=402,
            detail=msg(_insufficient_key(), user.language, cost=amount),
        )
    db.add(JetonTransaction(user_id=user.id, delta=-amount, reason=reason))


def _insufficient_key() -> str:
    """Mağazası olmayan platformda "mağazadan al" demek çıkmaz sokak. Satın alma
    kapalıysa kullanıcıya haftalık yenilemeyi anlatan metni veririz."""
    return (
        "jeton_insufficient_ai"
        if get_settings().billing_enabled
        else "jeton_insufficient_no_store"
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
