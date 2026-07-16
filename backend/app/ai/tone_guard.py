"""AI çıktısı kullanıcıya gösterilmeden önce ton kontrolü (CLAUDE.md §6).

Hedef kitle motivasyonu kırılgan, kendi kendine öğrenen çizerler. Bu katman:
1. Aşağılayıcı/sert ifadeleri yakalar ve yumuşatılmış genel ifadeyle değiştirir.
2. Her analizde en az bir güçlü yön bulunmasını garanti eder.
"""

from .schemas import LevelAssessment, RedlineResult, SkillAxis

# Bilerek geniş tutulmuş kaba/olumsuz kalıplar (Türkçe + İngilizce sızıntılara karşı)
_HARSH_PATTERNS = [
    "berbat", "kötü çizilmiş", "yanlışsın", "beceriksiz", "yeteneksiz", "vasat",
    "çirkin", "başarısız", "acemice", "kusurlu bir çizim",
    "terrible", "awful", "ugly", "bad drawing", "amateurish", "talentless",
]

_SOFT_REPLACEMENT = "Bu bölüm gelişime açık"
_FALLBACK_STRENGTH = "Bu çalışmayı tamamlayıp paylaşman başlı başına değerli bir adım."


def _soften(text: str) -> str:
    lowered = text.lower()
    for pattern in _HARSH_PATTERNS:
        if pattern in lowered:
            return _SOFT_REPLACEMENT + " — küçük dokunuşlarla toparlanır."
    return text


def guard_redline(result: RedlineResult) -> RedlineResult:
    for finding in result.findings:
        finding.message_tr = _soften(finding.message_tr)
        finding.suggestion_tr = _soften(finding.suggestion_tr)
    result.overall_comment_tr = _soften(result.overall_comment_tr)
    result.strengths_tr = [_soften(s) for s in result.strengths_tr]
    if not result.strengths_tr:
        result.strengths_tr = [_FALLBACK_STRENGTH]
    return result


def guard_assessment(result: LevelAssessment) -> LevelAssessment:
    result.summary_tr = _soften(result.summary_tr)
    # Model eksen atlayabiliyor — chart'ın 7 ekseni de her zaman dolu olmalı
    for axis in SkillAxis:
        result.ability_scores.setdefault(axis, 0)
    for axis, score in result.ability_scores.items():
        result.ability_scores[axis] = max(0, min(100, score))
    return result
