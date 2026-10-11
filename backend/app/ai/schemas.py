"""AI çıktılarının yapılandırılmış modelleri.

Koordinatlar 0-1 aralığında normalize edilir (görsel yeniden boyutlandırılsa da
overlay doğru yere düşer); frontend bunları piksel değerine çevirir.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SkillAxis(str, Enum):
    """Ability Chart eksenleri. Kesin liste CLAUDE.md §8'de açık soru —
    değişirse tek yer burası."""

    ANATOMI = "anatomi"
    PERSPEKTIF = "perspektif"
    ISIK_GOLGE = "isik_golge"
    ORAN = "oran"
    CIZGI_KALITESI = "cizgi_kalitesi"
    KOMPOZISYON = "kompozisyon"
    RENK = "renk"


class Severity(str, Enum):
    DUSUK = "dusuk"
    ORTA = "orta"
    YUKSEK = "yuksek"


class RedlineFinding(BaseModel):
    skill_axis: SkillAxis
    x: float = Field(ge=0, le=1, description="Bulgunun yatay konumu (0-1 normalize)")
    y: float = Field(ge=0, le=1, description="Bulgunun dikey konumu (0-1 normalize)")
    severity: Severity
    # _tr son eki geriye dönük uyumluluk — içerik kullanıcının dilinde üretilir
    message_tr: str = Field(description="Constructive, concrete observation (in the user's language)")
    suggestion_tr: str = Field(description="Actionable suggestion / exercise (in the user's language)")


class TaskCheck(BaseModel):
    """Ödevin tek bir başarı kriterinin çizimde karşılanma durumu."""

    criterion_tr: str = Field(description="The task requirement being checked (user's language)")
    status: str = Field(description="met | partial | missing")


class RedlineResult(BaseModel):
    """Saklanan / istemciye dönen analiz biçimi (tüm sağlayıcılar için ortak).

    Model bunu DOĞRUDAN doldurmaz: aşağıdaki *ModelOut şemalarını doldurur,
    sunucu `to_result()` ile buna çevirir. Ayrım iki sebepten: (1) JSON alan
    SIRASI modelin akıl yürütme sırasıdır — uyum analizinde önce gözlem, sonra
    karar gelmeli; (2) task_match sunucuda kontrol listesinden HESAPLANIR,
    modelin uydurduğu sayı kullanılmaz.
    """

    strengths_tr: list[str]
    findings: list[RedlineFinding]
    overall_comment_tr: str
    # 2026-10: bir sonraki çalışmada odaklanılacak tek şey (eski kayıtlarda None)
    next_step_tr: str | None = None
    # Ödev uyumu (2026-09) — serbest analizde ve eski kayıtlarda None
    task_match: int | None = None
    task_match_comment_tr: str | None = None
    # 2026-10: uyum kararının dayanağı (öğrenci neyin eksik olduğunu görür)
    drawing_description_tr: str | None = None
    subject_matches: bool | None = None
    task_checks: list[TaskCheck] | None = None


_STRENGTHS = Field(
    description="1-2 SPECIFIC strengths: what works and where (no empty praise)"
)
_FINDINGS = Field(
    description="At most 3 findings, most important first. Each: one-sentence "
    "observation of what and where + one concrete fix or exercise."
)
_OVERALL = Field(description="1-2 sentence overall reading of the drawing, calm and direct")
# Varsayılanlı: bu alanı atlayan bir model yüzünden tüm analiz düşmesin
_NEXT_STEP = Field(
    "", description="The ONE thing to focus on in the next drawing, as a concrete action"
)


class RedlineModelOut(BaseModel):
    """Modelin doldurduğu şema — serbest analiz (görev yok)."""

    strengths_tr: list[str] = _STRENGTHS
    findings: list[RedlineFinding] = _FINDINGS
    overall_comment_tr: str = _OVERALL
    next_step_tr: str = _NEXT_STEP

    def to_result(self) -> RedlineResult:
        data = self.model_dump()
        data["next_step_tr"] = data["next_step_tr"].strip() or None
        return RedlineResult(**data)


# Konu tutmuyorsa (ör. kupa istendi, portre çizildi) kriterler kısmen
# "karşılanmış" görünse bile puan bu tavanı geçemez.
SUBJECT_MISMATCH_CAP = 20
_CHECK_WEIGHT = {"met": 1.0, "partial": 0.5, "missing": 0.0}


def score_task(checks: list[TaskCheck], subject_matches: bool) -> int:
    """Kontrol listesinden 0-100 uyum puanı. Bilinmeyen durum 'missing' sayılır."""
    if not checks:
        score = 100 if subject_matches else 0
    else:
        total = sum(_CHECK_WEIGHT.get(c.status.strip().lower(), 0.0) for c in checks)
        score = round(100 * total / len(checks))
    if not subject_matches:
        score = min(score, SUBJECT_MISMATCH_CAP)
    return score


class TaskRedlineModelOut(BaseModel):
    """Modelin doldurduğu şema — ödevli analiz. Alan sırası BİLİNÇLİ: önce
    çizimde ne olduğunu tarif et, sonra konu eşleşmesine ve kriterlere karar
    ver, en son geri bildirimi yaz."""

    drawing_description_tr: str = Field(
        description="1-2 SHORT neutral sentences: what the drawing actually shows "
        "(subject, how many views/figures, angle). Observe before judging."
    )
    subject_matches: bool = Field(
        description="Is the drawing's main subject the one the task asks for?"
    )
    task_checks: list[TaskCheck] = Field(
        description="One entry per task success criterion, judged ONLY on presence "
        "in the drawing (not on quality)"
    )
    task_match_comment_tr: str = Field(
        description="1-2 sentences: which criteria are met and what is missing"
    )
    strengths_tr: list[str] = _STRENGTHS
    findings: list[RedlineFinding] = _FINDINGS
    overall_comment_tr: str = _OVERALL
    next_step_tr: str = _NEXT_STEP

    def to_result(self) -> RedlineResult:
        data = self.model_dump()
        data["next_step_tr"] = data["next_step_tr"].strip() or None
        data["task_match"] = score_task(self.task_checks, self.subject_matches)
        return RedlineResult(**data)


class ModerationVerdict(BaseModel):
    """Paylaşım öncesi içerik güvenlik kararı (topluluk/mentor'a giden görseller)."""

    is_safe: bool
    category: str = Field(
        description="ok | nudity | violence | hate | other (unsafe sebep kategorisi)"
    )


class AssignmentBrief(BaseModel):
    """AI'ın ürettiği kişisel ödev (düğüm başına bir kez üretilir, saklanır).

    2026-10: serbest metin yerine yapılandırılmış — anlaşılır olsun diye ve
    success_criteria_tr uyum analizinin kontrol listesi olsun diye. Metin hâli
    (eski istemciler + saklama) sunucuda `to_text()` ile üretilir.
    """

    goal_tr: str = Field(description="One plain sentence: what is practiced and why")
    steps_tr: list[str] = Field(
        description="3-4 short imperative steps: what to draw, how many, from which angle"
    )
    success_criteria_tr: list[str] = Field(
        description="2-4 checkable criteria visible in the finished drawing"
    )
    time_minutes: int = Field(description="Realistic time in minutes (15-45)")

    def clean(self) -> "AssignmentBrief":
        """Modelin sınır dışı çıktısını toparlar (boşlar atılır, sayılar sınırlanır)."""
        self.steps_tr = [s.strip() for s in self.steps_tr if s.strip()][:5]
        self.success_criteria_tr = [c.strip() for c in self.success_criteria_tr if c.strip()][:4]
        self.time_minutes = max(10, min(60, int(self.time_minutes or 30)))
        return self

    def to_text(self, language: str = "tr") -> str:
        en = language == "en"
        lines = [self.goal_tr.strip(), ""]
        lines += [f"{i}. {s}" for i, s in enumerate(self.steps_tr, 1)]
        if self.success_criteria_tr:
            lines += ["", "Success criteria:" if en else "Başarı kriterleri:"]
            lines += [f"- {c}" for c in self.success_criteria_tr]
        lines += ["", f"~{self.time_minutes} {'min' if en else 'dk'}"]
        return "\n".join(lines).strip()


class LevelAssessment(BaseModel):
    level: int = Field(ge=1, le=10, description="Başlangıç seviyesi")
    ability_scores: dict[SkillAxis, int] = Field(
        description="Eksen başına 0-100 skor (Ability Chart verisi)"
    )
    summary_tr: str = Field(description="Constructive summary shown to the user (in the user's language)")
    focus_axes: list[SkillAxis] = Field(
        description="Yetenek ağacında öncelikle yönlendirilecek zayıf alanlar"
    )
