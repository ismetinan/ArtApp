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


class RedlineResult(BaseModel):
    strengths_tr: list[str] = Field(
        description="Strengths of the drawing, in the user's language — at least one per analysis"
    )
    findings: list[RedlineFinding]
    overall_comment_tr: str = Field(
        description="Overall assessment with an encouraging closing, in the user's language"
    )


class AssignmentBrief(BaseModel):
    """AI'ın ürettiği kişisel ödev görevi (düğüm başına bir kez üretilir, saklanır)."""

    # _tr son eki geriye dönük uyumluluk — içerik kullanıcının dilinde üretilir
    assignment_tr: str = Field(
        description="Concrete, numbered-steps homework brief (in the user's language)"
    )


class LevelAssessment(BaseModel):
    level: int = Field(ge=1, le=10, description="Başlangıç seviyesi")
    ability_scores: dict[SkillAxis, int] = Field(
        description="Eksen başına 0-100 skor (Ability Chart verisi)"
    )
    summary_tr: str = Field(description="Constructive summary shown to the user (in the user's language)")
    focus_axes: list[SkillAxis] = Field(
        description="Yetenek ağacında öncelikle yönlendirilecek zayıf alanlar"
    )
