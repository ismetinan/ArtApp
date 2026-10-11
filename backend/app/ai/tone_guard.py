"""AI çıktısı kullanıcıya gösterilmeden önce ton kontrolü (CLAUDE.md §6).

Hedef kitle motivasyonu kırılgan, kendi kendine öğrenen çizerler. Bu katman:
1. Aşağılayıcı/sert ifadeleri yakalar ve yumuşatılmış genel ifadeyle değiştirir.
2. Her analizde en az bir güçlü yön bulunmasını garanti eder.
"""

from .schemas import LevelAssessment, RedlineResult, SkillAxis, score_task

MAX_FINDINGS = 3
_SEVERITY_ORDER = {"yuksek": 0, "orta": 1, "dusuk": 2}

# Bilerek geniş tutulmuş kaba/olumsuz kalıplar (Türkçe + İngilizce sızıntılara karşı)
_HARSH_PATTERNS = [
    "berbat", "kötü çizilmiş", "yanlışsın", "beceriksiz", "yeteneksiz", "vasat",
    "çirkin", "başarısız", "acemice", "kusurlu bir çizim",
    "terrible", "awful", "ugly", "bad drawing", "amateurish", "talentless",
]

_SOFT_REPLACEMENT = {
    "tr": "Bu bölüm gelişime açık — küçük dokunuşlarla toparlanır.",
    "en": "This area has room to grow — small adjustments will pull it together.",
}
_FALLBACK_STRENGTH = {
    "tr": "Bu çalışmayı tamamlayıp paylaşman başlı başına değerli bir adım.",
    "en": "Finishing this piece and sharing it is a valuable step in itself.",
}


def _lang(language: str) -> str:
    return language if language in _SOFT_REPLACEMENT else "tr"


def _soften(text: str, lang: str) -> str:
    lowered = text.lower()
    for pattern in _HARSH_PATTERNS:
        if pattern in lowered:
            return _SOFT_REPLACEMENT[lang]
    return text


def guard_redline(result: RedlineResult, language: str = "tr") -> RedlineResult:
    lang = _lang(language)
    for finding in result.findings:
        finding.message_tr = _soften(finding.message_tr, lang)
        finding.suggestion_tr = _soften(finding.suggestion_tr, lang)
    result.overall_comment_tr = _soften(result.overall_comment_tr, lang)
    result.strengths_tr = [_soften(s, lang) for s in result.strengths_tr]
    if not result.strengths_tr:
        result.strengths_tr = [_FALLBACK_STRENGTH[lang]]
    # Okunabilirlik (2026-10): en önemli bulgular önce, en fazla MAX_FINDINGS.
    # Model kurala uymayıp 5 bulgu döndürse de öğrenci 3'ten fazlasını görmez.
    result.findings = sorted(
        result.findings, key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 1)
    )[:MAX_FINDINGS]
    if result.next_step_tr:
        result.next_step_tr = _soften(result.next_step_tr, lang)
    if result.task_checks is not None:
        # Uyum puanı her zaman kontrol listesinden — modelin sayısı değil
        result.task_match = score_task(result.task_checks, bool(result.subject_matches))
    elif result.task_match is not None:
        # Eski biçim (tek sayı): 72.5 / aralık dışı değerleri toparla
        result.task_match = max(0, min(100, round(float(result.task_match))))
    if result.task_match_comment_tr:
        result.task_match_comment_tr = _soften(result.task_match_comment_tr, lang)
    return result


def guard_assessment(result: LevelAssessment, language: str = "tr") -> LevelAssessment:
    result.summary_tr = _soften(result.summary_tr, _lang(language))
    # Model eksen atlayabiliyor — chart'ın 7 ekseni de her zaman dolu olmalı
    for axis in SkillAxis:
        result.ability_scores.setdefault(axis, 0)
    for axis, score in result.ability_scores.items():
        result.ability_scores[axis] = max(0, min(100, score))
    return result
