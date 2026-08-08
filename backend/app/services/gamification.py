"""XP / seviye / eksen skoru mantığı — tek yerde ki dengeleme kolay olsun."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.tables import AbilityScore, AbilityHistory, User

XP_PER_LEVEL = 100
AXIS_BUMP_PER_NODE = 8  # ESKİ davranış: ders tamamlamanın sabit eksen katkısı


def level_for_xp(xp: int) -> int:
    return 1 + xp // XP_PER_LEVEL


def award_xp(user: User, amount: int) -> None:
    user.xp += amount
    user.level = level_for_xp(user.xp)


# --- Faz 3: chart'ı redline bulgularından besle (2026-08-08) -------------------
#
# Önceki hâlinde chart bir BECERİ ÖLÇÜSÜ değil İLERLEME ÇUBUĞU'ydu: her ders
# tamamlamada ilgili eksene sabit +8 ekleniyordu, kullanıcı iyi de çizse kötü de
# çizse sonuç aynıydı. Oysa redline çıktısı zaten eksen ve şiddet taşıyor
# (RedlineFinding.skill_axis / severity) — bu sinyal kullanılmadan atılıyordu.
#
# Yeni mantık: her analiz, dokunduğu eksenler için bir GÖZLEM üretir; skor bu
# gözleme doğru yumuşatılarak (EMA) kayar. Tek bir kötü çizim skoru dibe
# vurdurmaz, tek bir iyi çizim de zirveye çıkarmaz — eğilim ölçülür.

# Bir eksende bulgu yoksa ve o eksen çalışıldıysa "iyi" sayılır.
OBSERVED_CLEAN = 78
# Bulgu varsa en KÖTÜ şiddet belirleyicidir: ciddi bir hata, yanındaki üç küçük
# gözlemle ortalanıp yumuşatılmamalı.
OBSERVED_BY_SEVERITY = {"dusuk": 62, "orta": 45, "yuksek": 26}
# Yumuşatma katsayısı: yeni gözlemin ağırlığı. 0.30 ≈ son 3-4 analiz baskın.
EMA_ALPHA = 0.30


def observations_from_findings(
    findings: list[dict] | None, focus_axis: str | None
) -> dict[str, int]:
    """Redline bulgularından eksen → gözlem (0-100) çıkarır.

    Yalnız çizimin GERÇEKTEN bilgi verdiği eksenler döner:
    - bulgusu olan her eksen (en kötü şiddet belirler),
    - ödevin hedef ekseni (focus_axis) bulgusuz kaldıysa temiz sayılır.

    Bir çizim renk hakkında hiçbir şey söylemiyorsa renk skoru oynamamalı —
    yoksa chart yine gerçeği değil aktiviteyi ölçer.
    """
    worst: dict[str, int] = {}
    for f in findings or []:
        axis = f.get("skill_axis")
        if not axis:
            continue
        observed = OBSERVED_BY_SEVERITY.get(f.get("severity", "orta"), 45)
        # min: en kötü şiddet kazanır
        worst[axis] = min(worst.get(axis, 100), observed)
    if focus_axis and focus_axis not in worst:
        worst[focus_axis] = OBSERVED_CLEAN
    return worst


def bump_ability(
    db: Session,
    user: User,
    axis: str | None,
    amount: int = AXIS_BUMP_PER_NODE,
    findings: list[dict] | None = None,
) -> None:
    """Eksen skorlarını günceller.

    findings verilirse (yeni yol): bulgulardan gözlem çıkarılıp EMA ile kaydırılır.
    findings yoksa (eski senkron uç, geriye dönük): eski sabit +amount davranışı.
    """
    if findings is None:
        if axis is None:
            return
        _apply(db, user, axis, _score_of(db, user, axis) + amount, record=False)
        return

    for observed_axis, observed in observations_from_findings(findings, axis).items():
        current = _score_of(db, user, observed_axis)
        # İlk gözlemde geçmiş yok → doğrudan gözleme otur (onboarding skoru
        # varsa ondan yumuşatarak kayar).
        target = (
            observed
            if current == 0
            else round(current * (1 - EMA_ALPHA) + observed * EMA_ALPHA)
        )
        _apply(db, user, observed_axis, target, record=True)


def _score_of(db: Session, user: User, axis: str) -> int:
    row = db.execute(
        select(AbilityScore).where(
            AbilityScore.user_id == user.id, AbilityScore.axis == axis
        )
    ).scalar_one_or_none()
    return row.score if row is not None else 0


def _apply(db: Session, user: User, axis: str, value: int, record: bool) -> None:
    value = max(0, min(100, value))
    row = db.execute(
        select(AbilityScore).where(
            AbilityScore.user_id == user.id, AbilityScore.axis == axis
        )
    ).scalar_one_or_none()
    if row is None:
        row = AbilityScore(user_id=user.id, axis=axis, score=0)
        db.add(row)
    row.score = value
    if record:
        # Zaman serisi: "perspektifin 8 haftada 34 → 61" ancak geçmiş tutulursa
        # gösterilebilir. Yalnız ölçüme dayalı güncellemeler kaydedilir.
        db.add(AbilityHistory(user_id=user.id, axis=axis, score=value))
