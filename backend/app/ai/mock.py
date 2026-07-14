"""Deterministik sahte sağlayıcı — API anahtarı olmadan geliştirme ve test için.

Çıktılar sabittir ki testler güvenilir olsun; içerik gerçek Gemini çıktısının
şeklini ve tonunu taklit eder.
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


class MockAIProvider(AIProvider):
    async def assess_level(self, images: list[bytes]) -> LevelAssessment:
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
            summary_tr=(
                "Çizimlerinde güzel bir temel var. Çizgi kullanımın kararlı ve "
                "kompozisyon duygun gelişmeye açık. Önümüzdeki derslerde özellikle "
                f"{weakest[0].value.replace('_', ' ')} alanına odaklanarak hızlı "
                "ilerleme kaydedebilirsin."
            ),
            focus_axes=weakest,
        )

    async def redline_analysis(self, image: bytes, lesson_context: str) -> RedlineResult:
        return RedlineResult(
            strengths_tr=[
                "Genel siluet dengeli ve hareket hissi başarılı.",
                "Çizgi akıcılığında belirgin bir güven var.",
            ],
            findings=[
                RedlineFinding(
                    skill_axis=SkillAxis.ORAN,
                    x=0.42,
                    y=0.28,
                    severity=Severity.ORTA,
                    message_tr="Baş, gövdeye oranla biraz büyük görünüyor.",
                    suggestion_tr=(
                        "Figürü 7-8 baş boyu ölçüsüyle hafifçe bölerek kontrol etmeyi "
                        "dene; bir sonraki çizimde önce ölçü çizgilerini at."
                    ),
                ),
                RedlineFinding(
                    skill_axis=SkillAxis.PERSPEKTIF,
                    x=0.61,
                    y=0.55,
                    severity=Severity.DUSUK,
                    message_tr="Sol omuz çizgisi, gövdenin dönüşüyle tam uyuşmuyor.",
                    suggestion_tr=(
                        "Omuz ve kalça çizgilerini basit iki çubuk olarak çizip "
                        "açılarını karşılaştır — bu küçük kontrol dönüşü netleştirir."
                    ),
                ),
            ],
            overall_comment_tr=(
                f"'{lesson_context}' konusundaki bu çalışman sağlam bir adım. "
                "Yukarıdaki iki küçük noktaya odaklanırsan bir sonraki denemende "
                "farkı net göreceksin — devam et!"
            ),
        )
