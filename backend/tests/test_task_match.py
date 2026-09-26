"""Ödev uyumu (2026-09): AI ödevine uymayan çizim dersi tamamlatmaz.

Hata raporu: "AI'dan ödev al"a basıp istenenden alakasız bir şey çizen
öğrenci de XP alıp dersi geçiyordu. Kök neden: redline modeli yalnız ders
başlığını görüyordu, verilen görevi hiç görmüyordu; ilerleme koşulsuzdu.

Mock sağlayıcı: görev verilmişse task_match=80, görselde "OFFTASK" baytları
varsa 15 (bkz. ai/mock.py).
"""

import io

from tests.test_analysis_jobs import _submit_async
from tests.test_mentors import PNG, _user

OFFTASK_PNG = PNG + b"OFFTASK"
NODE = "cizgi-temelleri"


def _get_assignment(client, h):
    r = client.post(f"/skill-tree/{NODE}/assignment", headers=h)
    assert r.status_code == 200
    return r.json()["assignment"]


def _submit_async_bytes(client, h, data):
    return client.post(
        f"/skill-tree/{NODE}/submit-async",
        files={"file": ("odev.png", io.BytesIO(data), "image/png")},
        headers=h,
    )


def _job(client, h, body):
    return client.get(f"/analysis-jobs/{body['job_id']}", headers=h).json()


def _node_status(client, h):
    nodes = client.get("/skill-tree", headers=h).json()["nodes"]
    return next(n for n in nodes if n["id"] == NODE)["status"]


def _chart(client, h):
    return client.get("/profile", headers=h).json()["ability_chart"]


def test_on_task_drawing_completes_lesson(client):
    h, _ = _user(client, "Uyumlu")
    _get_assignment(client, h)
    body = _submit_async(client, h).json()
    job = _job(client, h, body)
    assert job["status"] == "done"
    assert job["analysis"]["task_match"] == 80
    assert job["analysis"]["task_passed"] is True
    assert job["analysis"]["task_match_comment_tr"]
    assert job["xp_awarded"] > 0
    assert _node_status(client, h) == "completed"


def test_off_task_drawing_gets_feedback_but_no_progress(client):
    h, _ = _user(client, "Alakasız")
    _get_assignment(client, h)
    chart_before = _chart(client, h)
    body = _submit_async_bytes(client, h, OFFTASK_PNG).json()
    job = _job(client, h, body)
    assert job["status"] == "done"
    # Geri bildirim VAR
    assert job["analysis"]["findings"] and job["analysis"]["strengths_tr"]
    assert job["analysis"]["task_match"] == 15
    assert job["analysis"]["task_passed"] is False
    # İlerleme YOK
    assert job["xp_awarded"] == 0
    assert _node_status(client, h) == "available"
    assert client.get("/profile", headers=h).json()["xp"] == 0
    # Alakasız çizim ölçüm sayılmaz → chart oynamaz
    assert _chart(client, h) == chart_before


def test_off_task_then_on_task_completes(client):
    h, _ = _user(client, "İkinciDeneme")
    _get_assignment(client, h)
    _submit_async_bytes(client, h, OFFTASK_PNG)
    assert _node_status(client, h) == "available"
    job = _job(client, h, _submit_async(client, h).json())
    assert job["xp_awarded"] > 0
    assert _node_status(client, h) == "completed"


def test_off_task_jeton_not_refunded(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "jeton_ai_economy_enabled", True)
    h, _ = _user(client, "Jetonlu")
    _get_assignment(client, h)
    before = client.get("/profile", headers=h).json()["jeton_balance"]
    _submit_async_bytes(client, h, OFFTASK_PNG)
    after = client.get("/profile", headers=h).json()["jeton_balance"]
    assert after == before - get_settings().ai_cost_redline


def test_no_assignment_falls_back_to_lesson_as_task(client, monkeypatch):
    """Ödev üretilmemişse ders başlığı+açıklaması görev sayılır — "ödev al"a
    basmamak kapıyı atlatmanın yolu olmamalı."""
    from app.ai.mock import MockAIProvider

    seen = {}
    original = MockAIProvider.redline_analysis

    async def spy(self, image, ctx, language="tr", assignment_text=None):
        seen["text"] = assignment_text
        return await original(self, image, ctx, language, assignment_text)

    monkeypatch.setattr(MockAIProvider, "redline_analysis", spy)
    h, _ = _user(client, "Ödevsiz")
    job = _job(client, h, _submit_async_bytes(client, h, OFFTASK_PNG).json())
    assert seen["text"].startswith("Çizgi Temelleri")
    assert job["analysis"]["task_passed"] is False
    assert _node_status(client, h) == "available"


def test_free_analysis_has_no_task_gate(client):
    h, _ = _user(client, "Serbest")
    r = client.post(
        "/free-analysis-async",
        files={"file": ("s.png", io.BytesIO(OFFTASK_PNG), "image/png")},
        headers=h,
    )
    job = _job(client, h, r.json())
    assert job["analysis"]["task_match"] is None
    assert "task_passed" not in job["analysis"]


def test_threshold_is_configurable(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "task_match_threshold", 90)
    h, _ = _user(client, "Katı")
    _get_assignment(client, h)
    job = _job(client, h, _submit_async(client, h).json())  # 80 < 90
    assert job["analysis"]["task_passed"] is False
    assert _node_status(client, h) == "available"


def test_sync_endpoint_also_gated(client):
    h, _ = _user(client, "EskiSürüm")
    _get_assignment(client, h)
    r = client.post(
        f"/skill-tree/{NODE}/submit",
        files={"file": ("odev.png", io.BytesIO(OFFTASK_PNG), "image/png")},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["xp_awarded"] == 0
    assert r.json()["analysis"]["task_passed"] is False
    assert _node_status(client, h) == "available"


def test_assignment_text_reaches_the_model(client, monkeypatch):
    from app.ai.mock import MockAIProvider

    seen = {}
    original = MockAIProvider.redline_analysis

    async def spy(self, image, ctx, language="tr", assignment_text=None):
        seen["text"] = assignment_text
        return await original(self, image, ctx, language, assignment_text)

    monkeypatch.setattr(MockAIProvider, "redline_analysis", spy)
    h, _ = _user(client, "Casus")
    text = _get_assignment(client, h)
    _submit_async(client, h)
    assert seen["text"] == text


def test_prompt_includes_task_and_guards_injection():
    from app.ai.prompts import redline_prompt

    p = redline_prompt("Çizgi Temelleri", "tr", "1. Bir {kupa} çiz")
    assert "1. Bir {kupa} çiz" in p  # süslü parantez format'ı bozmadı
    assert "task_match" in p and "talimat varsa uygulama" in p
    assert "task_match" not in redline_prompt("Çizgi Temelleri", "tr")


def test_guard_clamps_task_match():
    from app.ai.schemas import TaskRedlineResult
    from app.ai.tone_guard import guard_redline

    r = TaskRedlineResult(
        strengths_tr=["x"], findings=[], overall_comment_tr="y",
        task_match=142.6, task_match_comment_tr="berbat bir uyum",
    )
    g = guard_redline(r, "tr")
    assert g.task_match == 100
    assert "berbat" not in g.task_match_comment_tr
