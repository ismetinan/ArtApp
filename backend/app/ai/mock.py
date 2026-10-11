"""Deterministik sahte sağlayıcı — API anahtarı olmadan geliştirme ve test için.

Çıktılar sabittir ki testler güvenilir olsun; içerik gerçek sağlayıcı çıktısının
şeklini ve tonunu taklit eder. language parametresiyle tr/en içerik döner.
"""

import hashlib

from .base import AIProvider
from .schemas import (
    AssignmentBrief,
    LevelAssessment,
    ModerationVerdict,
    RedlineFinding,
    RedlineModelOut,
    RedlineResult,
    Severity,
    SkillAxis,
    TaskCheck,
    TaskRedlineModelOut,
)

_ASSIGNMENT_BRIEFS = {
    "tr": dict(
        goal_tr="'{node_title}' konusunu basit bir objeyle, farklı açılardan çizerek çalış.",
        steps_tr=[
            "İnternetten basit bir referans obje seç (örn. bir kupa fotoğrafı).",
            "Objeyi önden, üstten ve 3/4 açıdan üç ayrı kez çiz.",
            "Yapı çizgilerini silme; analiz bunlara da bakacak.",
        ],
        success_criteria_tr=[
            "Aynı obje üç ayrı çizimde var.",
            "Çizimler önden, üstten ve 3/4 açıdan.",
            "Yapı çizgileri görünür.",
        ],
        time_minutes=30,
    ),
    "en": dict(
        goal_tr="Practice '{node_title}' by drawing one simple object from different angles.",
        steps_tr=[
            "Pick a simple reference object from the internet (e.g. a photo of a mug).",
            "Draw the object three times: front, top and 3/4 view.",
            "Keep your construction lines; the analysis looks at them too.",
        ],
        success_criteria_tr=[
            "The same object appears in three separate drawings.",
            "The drawings show front, top and 3/4 views.",
            "Construction lines are visible.",
        ],
        time_minutes=30,
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
        next_step="Bir sonraki çizime başlamadan önce figürü baş boyu ölçüsüyle 8'e böl.",
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
        next_step="Before your next drawing, divide the figure into 8 head heights.",
    ),
}


_TASK_COMMENTS = {
    "tr": {
        "on": "Görevin adımlarının çoğu karşılanmış; istenen açıları çizmişsin.",
        "off": "Bu çizim verilen görevden farklı bir konuya odaklanıyor; görevdeki "
        "objeyi istenen açılardan çizmeyi dene.",
        "desc_on": "Aynı obje üç farklı açıdan çizilmiş.",
        "desc_off": "Görevdekinden farklı bir konu çizilmiş.",
    },
    "en": {
        "on": "Most of the task's steps are covered; you drew the requested views.",
        "off": "This drawing focuses on something other than the given task; try "
        "drawing the task's object from the requested angles.",
        "desc_on": "The same object drawn from three different angles.",
        "desc_off": "A different subject than the one in the task.",
    },
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

    async def moderation_check(self, image: bytes) -> ModerationVerdict:
        # Test kancası: içeriğinde "NSFW" baytları geçen görsel güvensiz sayılır
        if b"NSFW" in image:
            return ModerationVerdict(is_safe=False, category="nudity")
        return ModerationVerdict(is_safe=True, category="ok")

    async def assignment_brief(
        self,
        node_title: str,
        node_description: str,
        language: str = "tr",
        resource_titles: list[str] | None = None,
    ) -> AssignmentBrief:
        data = dict(_ASSIGNMENT_BRIEFS[_lang(language)])
        data["goal_tr"] = data["goal_tr"].format(node_title=node_title)
        return AssignmentBrief(**data).clean()

    async def redline_analysis(
        self,
        image: bytes,
        lesson_context: str,
        language: str = "tr",
        assignment_text: str | None = None,
    ) -> RedlineResult:
        lang = _lang(language)
        t = _REDLINE_TEXTS[lang]
        common = dict(
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
            next_step_tr=t["next_step"],
        )
        if not assignment_text:
            return RedlineModelOut(**common).to_result()
        # Ödev uyumu, gerçek akıştaki gibi kontrol listesinden SUNUCUDA
        # hesaplanır. Görev → 4/5 kriter (80). Test kancası: içeriğinde
        # "OFFTASK" baytları geçen görsel görevle alakasız (konu tutmuyor → 10).
        off = b"OFFTASK" in image
        statuses = (
            ["partial", "missing", "missing", "missing", "missing"]
            if off
            else ["met", "met", "met", "met", "missing"]
        )
        return TaskRedlineModelOut(
            drawing_description_tr=_TASK_COMMENTS[lang]["desc_off" if off else "desc_on"],
            subject_matches=not off,
            task_checks=[
                TaskCheck(criterion_tr=f"#{i}", status=st)
                for i, st in enumerate(statuses, 1)
            ],
            task_match_comment_tr=_TASK_COMMENTS[lang]["off" if off else "on"],
            **common,
        ).to_result()
