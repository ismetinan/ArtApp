"""Rozetler + çıkış kampanyası (2026-09).

Katalog burada; başlık/açıklama SUNUCUDA yerelleştirilir ki yeni rozet eklemek
mağaza güncellemesi gerektirmesin. İstemci `icon` anahtarını bir Material
ikonuna eşler, tanımadığı anahtarda varsayılan rozet ikonunu gösterir.

Değerlendirme tembel: /profile her açıldığında `evaluate` çağrılır ve henüz
verilmemiş, koşulu sağlanan rozetler eklenir (haftalık jeton damlasıyla aynı
desen). Yeni verilenler yanıtta `new_badges` olarak bir kez döner; istemci
kutlamayı buna göre gösterir.

Rozetler uygulamada HİÇBİR ŞEYİ AÇMAZ (kozmetik). Bu bilinçli: bağış
kuralının (CLAUDE.md, Apple §3.2.1) "hiçbir şey açmıyor" şartıyla ve jetonun
"yalnız uygulama içi AI birimi" tanımıyla çelişki riski olmasın.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.tables import (
    AbilityScore,
    JetonTransaction,
    Submission,
    User,
    UserActivityDay,
    UserBadge,
    UserProgress,
)
from . import jetons

FOUNDING = "founding_artist"
LAUNCH_BONUS_REASON = "launch_bonus"

# code → (icon, {lang: (başlık, açıklama)}). Sıra = profildeki gösterim sırası.
CATALOG: dict[str, tuple[str, dict[str, tuple[str, str]]]] = {
    FOUNDING: (
        "rocket",
        {
            "tr": ("Kurucu Çizer", "Artora'nın ilk günlerinde buradaydın."),
            "en": ("Founding Artist", "You were here in Artora's first days."),
        },
    ),
    "first_lesson": (
        "school",
        {
            "tr": ("İlk Adım", "İlk dersini tamamladın."),
            "en": ("First Step", "You completed your first lesson."),
        },
    ),
    "five_lessons": (
        "stairs",
        {
            "tr": ("Yolda", "5 ders tamamladın."),
            "en": ("On the Path", "You completed 5 lessons."),
        },
    ),
    "streak_7": (
        "fire",
        {
            "tr": ("7 Günlük Seri", "7 gün üst üste çalıştın."),
            "en": ("7-Day Streak", "You practiced 7 days in a row."),
        },
    ),
    "first_share": (
        "share",
        {
            "tr": ("Sahneye Çıktın", "Bir çizimini toplulukla paylaştın."),
            "en": ("On Stage", "You shared a drawing with the community."),
        },
    ),
    "axis_master": (
        "star",
        {
            "tr": ("Ustalık", "Bir beceri ekseninde 75 puanı geçtin."),
            "en": ("Mastery", "You passed 75 on a skill axis."),
        },
    ),
}

AXIS_MASTER_SCORE = 75
STREAK_DAYS = 7


def to_json(code: str, lang: str, awarded_at: datetime | None = None) -> dict:
    icon, texts = CATALOG[code]
    title, description = texts.get(lang) or texts["tr"]
    return {
        "code": code,
        "icon": icon,
        "title": title,
        "description": description,
        "awarded_at": awarded_at.isoformat() if awarded_at else None,
    }


def campaign_active(today: date | None = None) -> bool:
    until = get_settings().launch_campaign_until
    if until is None:
        return False
    return (today or datetime.now(timezone.utc).date()) <= until


def campaign_info(user: User) -> dict | None:
    """İstemcinin kampanya bandı için: aktifse bitiş tarihi + bonus. Misafirler
    burada "hesap oluştur, N jeton kazan" teşvikini görür."""
    s = get_settings()
    if not campaign_active():
        return None
    return {
        "until": s.launch_campaign_until.isoformat(),
        "bonus_jetons": s.launch_bonus_jetons,
        "bonus_requires_account": True,
    }


def _held(db: Session, user: User) -> set[str]:
    return set(
        db.execute(select(UserBadge.code).where(UserBadge.user_id == user.id)).scalars()
    )


def _streak(db: Session, user: User) -> int:
    """Bugün (ya da dün) biten ardışık aktif gün sayısı."""
    today = datetime.now(timezone.utc).date()
    days = set(
        db.execute(
            select(UserActivityDay.day).where(
                UserActivityDay.user_id == user.id,
                UserActivityDay.day > today - timedelta(days=STREAK_DAYS + 1),
            )
        ).scalars()
    )
    cursor = today if today in days else today - timedelta(days=1)
    n = 0
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def _earned(db: Session, user: User, held: set[str]) -> list[str]:
    """Koşulu sağlanan ama henüz verilmemiş ilerleme rozetleri."""
    out: list[str] = []

    def want(code: str) -> bool:
        return code not in held

    if want("first_lesson") or want("five_lessons"):
        lessons = db.execute(
            select(func.count()).select_from(UserProgress).where(
                UserProgress.user_id == user.id
            )
        ).scalar_one()
        if lessons >= 1 and want("first_lesson"):
            out.append("first_lesson")
        if lessons >= 5 and want("five_lessons"):
            out.append("five_lessons")
    if want("first_share"):
        shared = db.execute(
            select(Submission.id).where(
                Submission.user_id == user.id,
                Submission.is_public.is_(True),
                Submission.moderation_hidden.is_(False),
            )
        ).first()
        if shared is not None:
            out.append("first_share")
    if want("axis_master"):
        master = db.execute(
            select(AbilityScore.id).where(
                AbilityScore.user_id == user.id, AbilityScore.score >= AXIS_MASTER_SCORE
            )
        ).first()
        if master is not None:
            out.append("axis_master")
    if want("streak_7") and _streak(db, user) >= STREAK_DAYS:
        out.append("streak_7")
    return out


def _bonus_claimed(db: Session, user: User) -> bool:
    return (
        db.execute(
            select(JetonTransaction.id).where(
                JetonTransaction.user_id == user.id,
                JetonTransaction.reason == LAUNCH_BONUS_REASON,
            )
        ).first()
        is not None
    )


def evaluate(db: Session, user: User) -> tuple[list[str], int]:
    """Rozetleri ve kampanya jetonunu işler. (yeni rozet kodları, verilen
    kampanya jetonu) döner. Değişiklik olduysa çağıran commit eder.

    Kampanya jetonu çift verilmesin diye kullanıcı satırı kilitlenir (Postgres
    SELECT ... FOR UPDATE; SQLite yok sayar): eşzamanlı ikinci /profile isteği
    birincinin commit'ini bekler, sonra launch_bonus hareketini görüp vazgeçer.
    Rozet satırları savepoint içinde eklenir; yarışta UniqueConstraint'e
    takılan kopya sessizce atlanır.
    """
    held = _held(db, user)
    new: list[str] = []
    bonus = 0

    if campaign_active():
        amount = get_settings().launch_bonus_jetons
        wants_bonus = not user.is_guest and amount > 0 and not _bonus_claimed(db, user)
        if FOUNDING not in held or wants_bonus:
            db.execute(select(User.id).where(User.id == user.id).with_for_update())
            held = _held(db, user)  # kilit sonrası taze oku
            if FOUNDING not in held:
                new.append(FOUNDING)
            if wants_bonus and not _bonus_claimed(db, user):
                # Ücretsiz (paid=False): satın alınmış sayılmaz, haftalık taban
                # hesabında ücretsiz bakiyeye girer. Kampanya bitse de silinmez.
                jetons.grant(db, user, amount, LAUNCH_BONUS_REASON)
                bonus = amount

    new.extend(_earned(db, user, held | set(new)))
    awarded: list[str] = []
    for code in new:
        try:
            with db.begin_nested():
                db.add(UserBadge(user_id=user.id, code=code))
            awarded.append(code)
        except IntegrityError:
            pass  # eşzamanlı istek aynı rozeti az önce verdi
    return awarded, bonus


def list_for(db: Session, user: User) -> list[dict]:
    rows = db.execute(
        select(UserBadge.code, UserBadge.awarded_at).where(UserBadge.user_id == user.id)
    ).all()
    by_code = {r.code: r.awarded_at for r in rows if r.code in CATALOG}
    return [to_json(c, user.language, by_code[c]) for c in CATALOG if c in by_code]
