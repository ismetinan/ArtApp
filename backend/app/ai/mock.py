"""Deterministik sahte sağlayıcı — API anahtarı olmadan geliştirme ve test için.

Çıktılar sabittir ki testler güvenilir olsun; içerik gerçek sağlayıcı çıktısının
şeklini ve tonunu taklit eder. language parametresiyle tr/en içerik döner.
"""

import hashlib

from .base import AIProvider
from .schemas import (
    LevelAssessment,
    RedlineFinding,
    RedlineResult,
    Severity,
    SkillAxis,
)

_ASSESS_SUMMARY = {
    "tr": (
        "Çizimlerinde güzel bir temel var. Çizgi kullanımın kararlı ve "
        "kompozisyon duygun gelişmeye açık. Önümüzdeki derslerde özellikle "
        "{weakest} alanına odaklanarak hızlı ilerleme kaydedebilirsin."
    ),
    "en": (
        "There's a nice foundation in your drawings. Your line work is confident "
        "and your sense of composition has room to grow. Focusing especially on "
        "{weakest} in the upcoming lessons will help you improve quickly."
    ),
}

_REDLINE_TEXTS = {
    "tr": dict(
        strengths=[
            "Genel siluet dengeli ve hareket hissi başarılı.",
            "Çizgi akıcılığında belirgin bir güven var.",
        ],
        f1_message="Baş, gövdeye oranla biraz büyük görünüyor.",
        f1_suggestion=(
            "Figürü 7-8 baş boyu ölçüsüyle hafifçe bölerek kontrol etmeyi "
            "dene; bir sonraki çizimde önce ölçü çizgilerini at."
        ),
        f2_message="Sol omuz çizgisi, gövdenin dönüşüyle tam uyuşmuyor.",
        f2_suggestion=(
            "Omuz ve kalça çizgilerini basit iki çubuk olarak çizip "
            "açılarını karşılaştır — bu küçük kontrol dönüşü netleştirir."
        ),
        overall=(
            "'{lesson_context}' konusundaki bu çalışman sağlam bir adım. "
            "Yukarıdaki iki küçük noktaya odaklanırsan bir sonraki denemende "
            "farkı net göreceksin — devam et!"
        ),
    ),
    "en": dict(
        strengths=[
            "The overall silhouette is balanced and the sense of movement works well.",
            "There's clear confidence in the flow of your lines.",
        ],
        f1_message="The head looks slightly large in proportion to the torso.",
        f1_suggestion=(
            "Try lightly dividing the figure with a 7-8 head-height measure; "
            "in your next drawing, lay down the measuring lines first."
        ),
        f2_message="The left shoulder line doesn't quite match the turn of the torso.",
        f2_suggestion=(
            "Draw the shoulder and hip lines as two simple bars and compare "
            "their angles — that small check will clarify the rotation."
        ),
        overall=(
            "This piece on '{lesson_context}' is a solid step. Focus on the two "
            "small points above and you'll clearly see the difference in your "
            "next attempt — keep going!"
        ),
    ),
}


def _lang(language: str) -> str:
    return language if language in _REDLINE_TEXTS else "tr"


class MockAIProvider(AIProvider):
    async def assess_level(
        self, images: list[bytes], language: str = "tr"
    ) -> LevelAssessment:
        # Görsel içeriğine göre deterministik ama sabit-görünümlü skorlar üret
        seed = int(hashlib.sha256(b"".join(images)).hexdigest(), 16)
        base = 30 + seed % 25
        scores = {
            axis: min(100, base + (i * 7) % 30) for i, axis in enumerate(SkillAxis)
        }
        weakest = sorted(scores, key=scores.get)[:2]
        return LevelAssessment(
            level=max(1, base // 15),
            ability_scores=scores,
            summary_tr=_ASSESS_SUMMARY[_lang(language)].format(
                weakest=weakest[0].value.replace("_", " ")
            ),
            focus_axes=weakest,
        )

    async def redline_analysis(
        self, image: bytes, lesson_context: str, language: str = "tr"
    ) -> RedlineResult:
        t = _REDLINE_TEXTS[_lang(language)]
        return RedlineResult(
            strengths_tr=list(t["strengths"]),
            findings=[
                RedlineFinding(
                    skill_axis=SkillAxis.ORAN,
                    x=0.42,
                    y=0.28,
                    severity=Severity.ORTA,
                    message_tr=t["f1_message"],
                    suggestion_tr=t["f1_suggestion"],
                ),
                RedlineFinding(
                    skill_axis=SkillAxis.PERSPEKTIF,
                    x=0.61,
                    y=0.55,
                    severity=Severity.DUSUK,
                    message_tr=t["f2_message"],
                    suggestion_tr=t["f2_suggestion"],
                ),
            ],
            overall_comment_tr=t["overall"].format(lesson_context=lesson_context),
        )
