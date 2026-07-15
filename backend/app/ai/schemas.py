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
    message_tr: str = Field(description="Yapıcı, somut gözlem (Türkçe)")
    suggestion_tr: str = Field(description="Uygulanabilir öneri / egzersiz (Türkçe)")


class RedlineResult(BaseModel):
    strengths_tr: list[str] = Field(description="Çizimin güçlü yönleri — her analizde en az bir tane")
    findings: list[RedlineFinding]
    overall_comment_tr: str = Field(description="Genel değerlendirme, cesaretlendirici kapanış")


class LevelAssessment(BaseModel):
    level: int = Field(ge=1, le=10, description="Başlangıç seviyesi")
    ability_scores: dict[SkillAxis, int] = Field(
        description="Eksen başına 0-100 skor (Ability Chart verisi)"
    )
    summary_tr: str = Field(description="Kullanıcıya gösterilecek yapıcı özet")
    focus_axes: list[SkillAxis] = Field(
        description="Yetenek ağacında öncelikle yönlendirilecek zayıf alanlar"
    )
