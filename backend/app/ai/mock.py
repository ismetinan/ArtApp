"""Deterministik sahte sağlayıcı — API anahtarı olmadan geliştirme ve test için.

Çıktılar sabittir ki testler güvenilir olsun; içerik gerçek sağlayıcı çıktısının
şeklini ve tonunu taklit eder. language parametresiyle tr/en içerik döner.
"""

import hashlib

from .base import AIProvider
from .schemas import (
    AssignmentBrief,
    LevelAssessment,
    RedlineFinding,
    RedlineResult,
    Severity,
    SkillAxis,
)

_ASSIGNMENT_TEXTS = {
    "tr": (
        "'{node_title}' ödevi:\n"
        "1. İnternetten basit bir referans obje seç (örn. bir kupa fotoğrafı).\n"
        "2. Objeyi önden, üstten ve 3/4 açıdan üç ayrı kez çiz.\n"
        "3. Her çizimde yapı çizgilerini silmeden bırak — analiz bunlara bakacak.\n"
        "Bitince tek fotoğrafta yükle."
    ),
    "en": (
        "Assignment for '{node_title}':\n"
        "1. Pick a simple reference object from the internet (e.g. a photo of a mug).\n"
        "2. Draw the object three times: front, top and 3/4 view.\n"
        "3. Leave your construction lines visible — the analysis will look at them.\n"
        "Upload a single photo when done."
    ),
}

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

    async def assignment_brief(
        self, node_title: str, node_description: str, language: str = "tr"
    ) -> AssignmentBrief:
        return AssignmentBrief(
            assignment_tr=_ASSIGNMENT_TEXTS[_lang(language)].format(node_title=node_title)
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
