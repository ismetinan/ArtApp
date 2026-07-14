"""Ton koruması: AI çıktısı kırıcı ifade içerse bile kullanıcıya ulaşmamalı."""

from app.ai import RedlineFinding, RedlineResult, Severity, SkillAxis, guard_redline


def _result(**overrides):
    base = dict(
        strengths_tr=["Kompozisyon dengeli."],
        findings=[
            RedlineFinding(
                skill_axis=SkillAxis.ANATOMI,
                x=0.5,
                y=0.5,
                severity=Severity.ORTA,
                message_tr="El anatomisi berbat olmuş.",
                suggestion_tr="El etütleri çalış.",
            )
        ],
        overall_comment_tr="Devam et!",
    )
    base.update(overrides)
    return RedlineResult(**base)


def test_harsh_message_softened():
    result = guard_redline(_result())
    assert "berbat" not in result.findings[0].message_tr.lower()
    assert "gelişime açık" in result.findings[0].message_tr


def test_empty_strengths_gets_fallback():
    result = guard_redline(_result(strengths_tr=[]))
    assert len(result.strengths_tr) == 1


def test_clean_output_untouched():
    result = guard_redline(_result())
    assert result.overall_comment_tr == "Devam et!"
    assert result.strengths_tr == ["Kompozisyon dengeli."]
