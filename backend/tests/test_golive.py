"""Go-live özellikleri: Google girişi, hesap silme, AI kotası, yükleme sınırı, /privacy."""

import io

from tests.test_mvp_flow import PNG, _guest, _png_file


def _mock_google(monkeypatch, sub="google-sub-1", email="g@example.com", name="Google Çizer"):
    monkeypatch.setattr(
        "app.api.users.verify_google_token",
        lambda token: {"sub": sub, "email": email, "name": name},
    )


def test_google_new_user_then_login(client, monkeypatch):
    _mock_google(monkeypatch)
    r = client.post("/users/google", json={"id_token": "fake"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_guest"] is False
    first_id = body["id"]

    # İkinci giriş: aynı kullanıcı, yeni token
    r2 = client.post("/users/google", json={"id_token": "fake"})
    assert r2.json()["id"] == first_id
    assert r2.json()["token"] != body["token"]


def test_google_upgrades_guest_keeping_progress(client, monkeypatch):
    _mock_google(monkeypatch, sub="google-sub-2", email="g2@example.com")
    headers = _guest(client)
    r = client.post(
        "/onboarding/assess",
        files=[("files", _png_file(f"c{i}.png")) for i in range(3)],
        headers=headers,
    )
    assert r.status_code == 200

    r = client.post("/users/google", json={"id_token": "fake"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["is_guest"] is False

    new_headers = {"Authorization": f"Bearer {r.json()['token']}"}
    profile = client.get("/profile", headers=new_headers).json()
    assert len(profile["ability_chart"]) == 7  # ilerleme korundu


def test_google_links_existing_email_account(client, monkeypatch):
    r = client.post(
        "/users/register",
        json={"email": "ayni@example.com", "password": "sifre12345", "display_name": "A"},
    )
    existing_id = r.json()["id"]
    _mock_google(monkeypatch, sub="google-sub-3", email="ayni@example.com")
    r = client.post("/users/google", json={"id_token": "fake"})
    assert r.json()["id"] == existing_id


def test_google_invalid_token_401(client, monkeypatch):
    def _raise(token):
        raise ValueError("bozuk token")

    monkeypatch.setattr("app.api.users.verify_google_token", _raise)
    r = client.post("/users/google", json={"id_token": "sahte"})
    assert r.status_code == 401


def test_delete_account_removes_everything(client):
    headers = _guest(client)
    r = client.post(
        "/onboarding/assess",
        files=[("files", _png_file(f"c{i}.png")) for i in range(3)],
        headers=headers,
    )
    assert r.status_code == 200

    r = client.delete("/users/me", headers=headers)
    assert r.status_code == 200 and r.json() == {"deleted": True}
    # Token artık geçersiz
    assert client.get("/profile", headers=headers).status_code == 401


def test_ai_daily_quota_429(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ai_daily_limit", 2)
    headers = _guest(client)
    # 1. hak: onboarding
    r = client.post(
        "/onboarding/assess",
        files=[("files", _png_file(f"c{i}.png")) for i in range(3)],
        headers=headers,
    )
    assert r.status_code == 200
    # 2. hak: ödev
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 200
    # 3. istek: kota dolu
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 429
    assert "hakkın doldu" in r.json()["detail"]


def test_upload_size_cap_422(client):
    headers = _guest(client)
    big = PNG + b"\x00" * (8 * 1024 * 1024)
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit",
        files={"file": ("dev.png", io.BytesIO(big), "image/png")},
        headers=headers,
    )
    assert r.status_code == 422
    assert "8 MB" in r.json()["detail"]


def test_privacy_page(client):
    r = client.get("/privacy")
    assert r.status_code == 200
    assert "Gizlilik" in r.text


def test_partial_ai_axes_still_yield_full_chart(client, monkeypatch):
    """Model eksen atlarsa guard 0 ile doldurmalı, profil 7 ekseni de dönmeli."""
    from app.ai.schemas import LevelAssessment, SkillAxis
    from app.ai.tone_guard import guard_assessment

    partial = LevelAssessment(
        level=2,
        ability_scores={SkillAxis.ANATOMI: 40, SkillAxis.CIZGI_KALITESI: 55},
        summary_tr="Güzel bir başlangıç.",
        focus_axes=[SkillAxis.ANATOMI],
    )
    guarded = guard_assessment(partial)
    assert set(guarded.ability_scores) == set(SkillAxis)
    assert guarded.ability_scores[SkillAxis.RENK] == 0
    assert guarded.ability_scores[SkillAxis.CIZGI_KALITESI] == 55


def test_profile_chart_fills_missing_axes(client):
    """Tek eksen skoru olan kullanıcıda (örn. sadece ödevden bump) chart 7 eksen döner."""
    headers = _guest(client)
    # Onboarding yok; doğrudan bir ödevle tek eksene skor yaz
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 200
    chart = client.get("/profile", headers=headers).json()["ability_chart"]
    assert len(chart) == 7
    assert chart["cizgi_kalitesi"] > 0
    assert chart["renk"] == 0


def test_profile_chart_empty_before_onboarding(client):
    """Hiç skor yokken chart boş kalmalı — onboarding yönlendirmesi buna bakıyor."""
    headers = _guest(client)
    chart = client.get("/profile", headers=headers).json()["ability_chart"]
    assert chart == {}
