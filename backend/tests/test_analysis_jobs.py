"""Faz 2 (asenkron analiz) + Faz 3 (chart'ı bulgulardan besle).

Faz 2'nin can alıcı noktası JETON İADESİ: senkron akışta AI patlayınca harcama
transaction rollback'iyle geri sarılıyordu. Asenkronda yükleme ayrı commit
olduğu için iade AÇIKÇA yapılmak zorunda — aksi halde kullanıcı hiç analiz
almadan jeton kaybeder.

Not: TestClient, BackgroundTasks'i yanıt dönmeden önce çalıştırıyor; bu yüzden
testlerde iş çoğunlukla `done` olarak görünür.
"""

import io
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_mentors import PNG, _user


@pytest.fixture
def economy(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "jeton_ai_economy_enabled", True)
    return s


def _balance(client, h) -> int:
    return client.get("/profile", headers=h).json()["jeton_balance"]


def _submit_async(client, h, node="cizgi-temelleri"):
    return client.post(
        f"/skill-tree/{node}/submit-async",
        files={"file": ("odev.png", io.BytesIO(PNG), "image/png")},
        headers=h,
    )


def _break_ai(monkeypatch):
    async def boom(*a, **kw):
        raise RuntimeError("model meşgul")

    from app.ai.mock import MockAIProvider

    monkeypatch.setattr(MockAIProvider, "redline_analysis", boom)


def _findings(*pairs):
    """(eksen, şiddet) çiftlerinden sahte redline bulguları."""
    return [
        {"skill_axis": a, "severity": s, "x": 0.5, "y": 0.5,
         "message_tr": "m", "suggestion_tr": "s"}
        for a, s in pairs
    ]


def _fake_redline(monkeypatch, findings):
    """MockAIProvider'ın verilen bulguları döndürmesini sağlar."""
    from app.ai.mock import MockAIProvider
    from app.ai.schemas import RedlineResult

    async def fake(self, *a, **kw):
        return RedlineResult.model_validate(
            {
                "strengths_tr": ["Çizgilerin kararlı."],
                "findings": findings,
                "overall_comment_tr": "Güzel ilerliyorsun, böyle devam.",
            }
        )

    monkeypatch.setattr(MockAIProvider, "redline_analysis", fake)


# ---------- Faz 2: iş akışı ----------


def test_submit_async_returns_job_and_completes(client, economy):
    h, _ = _user(client, "Asenkron")
    r = _submit_async(client, h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_id"] > 0
    assert body["submission_id"] > 0

    job = client.get(f"/analysis-jobs/{body['job_id']}", headers=h).json()
    assert job["status"] == "done"
    assert job["analysis"] is not None
    assert job["xp_awarded"] > 0  # ilk tamamlama XP verir
    assert job["error"] is None


def test_result_is_persisted_on_submission(client, economy):
    """Analiz Submission'a da yazılır — Gelişim Macerası oradan besleniyor."""
    from app import db as db_module
    from app.models.tables import Submission

    h, _ = _user(client, "Kalıcı")
    sid = _submit_async(client, h).json()["submission_id"]
    with db_module.SessionLocal() as s:
        assert s.get(Submission, sid).ai_result is not None


def test_failed_job_refunds_the_jeton(client, economy, monkeypatch):
    """EN KRİTİK TEST: AI patlarsa jeton iade edilir.

    Senkron akışta bunu rollback yapıyordu; asenkronda açık iade şart."""
    h, _ = _user(client, "İade")
    assert _balance(client, h) == 3
    _break_ai(monkeypatch)

    body = _submit_async(client, h).json()
    job = client.get(f"/analysis-jobs/{body['job_id']}", headers=h).json()
    assert job["status"] == "failed"
    assert job["error"]  # yerelleştirilmiş hata metni
    assert _balance(client, h) == 3  # harcanan jeton geri geldi


def test_refund_is_not_doubled(client, economy, monkeypatch):
    """fail_stale ile runner aynı işi düşürmeye kalkarsa iade iki kez olmamalı."""
    from app import db as db_module
    from app.models.tables import AnalysisJob
    from app.services import analysis_jobs

    h, _ = _user(client, "ÇiftİadeYok")
    _break_ai(monkeypatch)
    body = _submit_async(client, h).json()
    assert _balance(client, h) == 3

    with db_module.SessionLocal() as s:
        job = s.get(AnalysisJob, body["job_id"])
        analysis_jobs.mark_failed(s, job, "ai_unavailable")  # ikinci kez
        s.commit()
    assert _balance(client, h) == 3  # hâlâ 3, 4 değil


def test_only_one_job_at_a_time(client, economy, monkeypatch):
    """Devam eden analiz varken ikinci yükleme 409 — çift jeton harcamayı önler."""
    from app import db as db_module
    from app.models.tables import AnalysisJob

    h, _ = _user(client, "TekIs")
    body = _submit_async(client, h).json()
    # İşi elle "running"a çekip devam ediyormuş gibi yap
    with db_module.SessionLocal() as s:
        job = s.get(AnalysisJob, body["job_id"])
        job.status = "running"
        s.commit()

    r = _submit_async(client, h, node="cizgi-temelleri")
    assert r.status_code == 409
    assert _balance(client, h) == 2  # ikinci istek jeton harcamadı


def test_stale_job_is_failed_and_refunded(client, economy):
    """Süreç ölüp iş 'running' kalırsa tembel zaman aşımı iade eder."""
    from app import db as db_module
    from app.models.tables import AnalysisJob

    h, _ = _user(client, "Takılı")
    body = _submit_async(client, h).json()
    with db_module.SessionLocal() as s:
        job = s.get(AnalysisJob, body["job_id"])
        job.status = "running"
        job.refunded = False
        job.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        s.commit()

    before = _balance(client, h)
    job = client.get(f"/analysis-jobs/{body['job_id']}", headers=h).json()
    assert job["status"] == "failed"
    assert _balance(client, h) == before + 1


def test_latest_job_endpoint_recovers_result(client, economy):
    """Kurtarma ucu: uygulama analiz sırasında kapansa da sonucu burada bulur."""
    h, _ = _user(client, "Kurtarma")
    body = _submit_async(client, h).json()
    latest = client.get("/analysis-jobs/latest", headers=h).json()["job"]
    assert latest["job_id"] == body["job_id"]
    assert latest["status"] == "done"
    assert latest["analysis"] is not None


def test_job_of_another_user_is_404(client, economy):
    h1, _ = _user(client, "Sahip")
    h2, _ = _user(client, "Yabancı")
    job_id = _submit_async(client, h1).json()["job_id"]
    assert client.get(f"/analysis-jobs/{job_id}", headers=h2).status_code == 404


def test_insufficient_jeton_creates_no_job(client, economy):
    from app import db as db_module
    from app.models.tables import AnalysisJob

    h, _ = _user(client, "Bakiyesiz")
    for _ in range(3):
        assert _submit_async(client, h).status_code == 200
    r = _submit_async(client, h)
    assert r.status_code == 402
    with db_module.SessionLocal() as s:
        assert s.query(AnalysisJob).count() == 3  # 4.'sü yazılmadı


def test_sync_endpoint_still_works(client, economy):
    """Play'deki eski sürümler senkron ucu çağırmaya devam ediyor."""
    h, _ = _user(client, "EskiIstemci")
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit",
        files={"file": ("odev.png", io.BytesIO(PNG), "image/png")},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["analysis"] is not None


# ---------- Faz 3: chart gerçekten ölçüyor ----------


def _axis(client, h, axis) -> int:
    return client.get("/profile", headers=h).json()["ability_chart"].get(axis, 0)


def test_severe_finding_lowers_axis_score(client, economy, monkeypatch):
    """Kötü çizim skoru AŞAĞI çeker — eski sabit +8 mantığında imkânsızdı."""
    h, _ = _user(client, "Kötü")
    _fake_redline(monkeypatch, _findings(("perspektif", "yuksek")))
    _submit_async(client, h)
    low = _axis(client, h, "perspektif")

    h2, _ = _user(client, "İyi")
    _fake_redline(monkeypatch, _findings(("perspektif", "dusuk")))
    _submit_async(client, h2)
    high = _axis(client, h2, "perspektif")

    assert low < high, f"ciddi bulgu daha düşük skor vermeli: {low} vs {high}"


def test_clean_drawing_scores_focus_axis_high(client, economy, monkeypatch):
    """Hedef eksende bulgu yoksa o eksen temiz sayılır."""
    h, _ = _user(client, "Temiz")
    _fake_redline(monkeypatch, [])
    _submit_async(client, h)  # cizgi-temelleri → cizgi_kalitesi ekseni
    assert _axis(client, h, "cizgi_kalitesi") >= 70


def test_untouched_axis_does_not_move(client, economy, monkeypatch):
    """Çizim renk hakkında bir şey söylemiyorsa renk skoru oynamamalı —
    yoksa chart yine gerçeği değil aktiviteyi ölçer."""
    h, _ = _user(client, "Dokunulmamış")
    _fake_redline(monkeypatch, _findings(("perspektif", "orta")))
    _submit_async(client, h)
    assert _axis(client, h, "renk") == 0


def test_repeat_practice_updates_chart_without_xp(client, economy, monkeypatch):
    """Tekrar pratik XP vermez ama chart'ı GÜNCELLER — gelişim ölçümü
    tekrardan doğar (eski davranışta ikinci deneme hiçbir şey yapmıyordu)."""
    h, _ = _user(client, "Tekrar")
    _fake_redline(monkeypatch, _findings(("cizgi_kalitesi", "yuksek")))
    first = _submit_async(client, h).json()
    assert first["job_id"]
    after_bad = _axis(client, h, "cizgi_kalitesi")

    # Aynı düğüme ikinci, daha iyi deneme
    _fake_redline(monkeypatch, [])
    second = _submit_async(client, h).json()
    job = client.get(f"/analysis-jobs/{second['job_id']}", headers=h).json()
    assert job["xp_awarded"] == 0  # ikinci tamamlama XP vermez
    assert _axis(client, h, "cizgi_kalitesi") > after_bad  # ama chart iyileşti


def test_ability_history_is_recorded(client, economy, monkeypatch):
    """Zaman serisi olmadan 'perspektifin 34 → 61' anlatısı kurulamaz."""
    from app import db as db_module
    from app.models.tables import AbilityHistory

    h, _ = _user(client, "Geçmiş")
    _fake_redline(monkeypatch, _findings(("perspektif", "orta")))
    _submit_async(client, h)
    with db_module.SessionLocal() as s:
        rows = s.query(AbilityHistory).filter_by(axis="perspektif").all()
        assert len(rows) >= 1
        assert 0 <= rows[0].score <= 100


def test_score_moves_gradually_not_in_jumps(client, economy, monkeypatch):
    """EMA: tek bir kötü çizim skoru dibe vurdurmamalı, eğilim ölçülmeli."""
    h, _ = _user(client, "Yumuşak")
    _fake_redline(monkeypatch, [])
    _submit_async(client, h)
    good = _axis(client, h, "cizgi_kalitesi")

    _fake_redline(monkeypatch, _findings(("cizgi_kalitesi", "yuksek")))
    _submit_async(client, h)
    after_one_bad = _axis(client, h, "cizgi_kalitesi")

    assert after_one_bad < good           # düştü
    assert after_one_bad > 40             # ama dibe vurmadı
