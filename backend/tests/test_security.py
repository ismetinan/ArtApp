"""Güvenlik denetimi düzeltmelerinin testleri (2026-07-19):

- API token'ları DB'de SHA-256 hash olarak durur, ham token yine çalışır
- Login brute-force hız limiti (IP başına)
- Yükleme magic-byte kontrolü (uzantısı .png yapılmış rastgele dosya reddedilir)
- Google girişinde doğrulanmamış e-posta mevcut hesaba BAĞLANMAZ
- Girdi uzunluk sınırları + güvenlik başlıkları
"""

import io

from tests.test_mentors import PNG, _user


def test_api_token_stored_hashed_but_raw_works(client):
    h, data = _user(client, "Hashli")
    raw = data["token"]

    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import User
    from app.services.auth import hash_token

    with db_module.SessionLocal() as s:
        u = s.execute(select(User).where(User.id == data["id"])).scalar_one()
        assert u.api_token != raw  # ham token DB'de YOK
        assert u.api_token == hash_token(raw)

    # Ham token'la kimlik doğrulama çalışır; hash'in kendisi bearer olarak İŞLEMEZ
    assert client.get("/profile", headers=h).status_code == 200
    stolen = {"Authorization": f"Bearer {hash_token(raw)}"}
    assert client.get("/profile", headers=stolen).status_code == 401


def test_login_rate_limited(client, monkeypatch):
    from app.core import ratelimit
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    ratelimit._BUCKETS.clear()

    body = {"email": "yok@example.com", "password": "yanlis-sifre"}
    for _ in range(10):
        assert client.post("/users/login", json=body).status_code == 401
    r = client.post("/users/login", json=body)
    assert r.status_code == 429
    assert "bekle" in r.json()["detail"]
    ratelimit._BUCKETS.clear()


def test_upload_must_be_real_image(client):
    h, _ = _user(client, "Sahteci")
    fake = b"<html><script>alert(1)</script></html>"
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit",
        files={"file": ("zarasiz.png", io.BytesIO(fake), "image/png")},
        headers=h,
    )
    assert r.status_code == 422
    assert "görsel değil" in r.json()["detail"]


def test_google_unverified_email_cannot_take_over_account(client, monkeypatch):
    # Kurban normal yolla kayıt olur
    r = client.post(
        "/users/register",
        json={"email": "kurban@example.com", "password": "gizli12345",
              "display_name": "Kurban"},
    )
    victim_id = r.json()["id"]

    # Saldırganın Google hesabında aynı e-posta DOĞRULANMAMIŞ →
    # verify_google_token email'i None döner (auth.py'deki email_verified koşulu)
    from app.api import users as users_module

    monkeypatch.setattr(
        users_module,
        "verify_google_token",
        lambda t: {"sub": "attacker-sub-1", "email": None, "name": "Saldırgan"},
    )
    r = client.post("/users/google", json={"id_token": "sahte"})
    assert r.status_code == 200
    attacker = r.json()
    # Kurbanın hesabı DEĞİL — yeni, ayrı bir hesap açıldı
    assert attacker["id"] != victim_id
    assert attacker["display_name"] == "Saldırgan"

    # Kurban şifresiyle girmeye devam edebiliyor
    r = client.post(
        "/users/login",
        json={"email": "kurban@example.com", "password": "gizli12345"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == victim_id


def test_verify_google_token_drops_unverified_email(monkeypatch):
    from app.core.config import get_settings
    from app.services import auth

    monkeypatch.setattr(get_settings(), "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: {
            "sub": "s1", "email": "e@example.com", "email_verified": False,
            "name": "X",
        },
    )
    assert auth.verify_google_token("t")["email"] is None
    monkeypatch.setattr(
        auth.google_id_token,
        "verify_oauth2_token",
        lambda *a, **k: {
            "sub": "s1", "email": "e@example.com", "email_verified": True,
            "name": "X",
        },
    )
    assert auth.verify_google_token("t")["email"] == "e@example.com"


def test_input_length_caps_and_security_headers(client):
    # 60 karakteri aşan görünen ad 422 (DB'ye 500'le düşmek yerine)
    r = client.post("/users/guest", json={"display_name": "x" * 200})
    assert r.status_code == 422

    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
