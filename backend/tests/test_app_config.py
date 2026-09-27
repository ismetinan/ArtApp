"""Güncelleme uyarısı yapılandırması (2026-09)."""


def test_defaults_no_prompt(client):
    r = client.get("/app-config?platform=android")
    assert r.status_code == 200
    body = r.json()
    assert body["latest_version"] is None and body["min_version"] is None
    assert body["store_url"].endswith("id=com.ismetinan.artapp")


def test_platform_specific_thresholds(client, monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "app_latest_version_android", "1.2.0")
    monkeypatch.setattr(s, "app_min_version_android", "1.1.0")
    monkeypatch.setattr(s, "app_latest_version_ios", "1.1.0")
    android = client.get("/app-config?platform=android").json()
    ios = client.get("/app-config?platform=ios").json()
    assert (android["latest_version"], android["min_version"]) == ("1.2.0", "1.1.0")
    # iOS henüz 1.2'yi yayınlamadıysa ona önerilmez; zorunlu eşik yok
    assert (ios["latest_version"], ios["min_version"]) == ("1.1.0", None)
    assert ios["store_url"].startswith("https://apps.apple.com/")


def test_no_auth_required(client):
    assert client.get("/app-config").status_code == 200
