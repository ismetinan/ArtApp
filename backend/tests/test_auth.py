"""Kayıt / giriş / misafir yükseltme / görsel gizliliği / AI hata dayanıklılığı."""

import io

from .test_mvp_flow import PNG, _guest, _png_file


def _register(client, email="cizer@example.com", password="cokgizli123"):
    return client.post(
        "/users/register",
        json={"email": email, "password": password, "display_name": "Kayıtlı Çizer"},
    )


def test_register_and_login(client):
    r = _register(client)
    assert r.status_code == 200
    assert r.json()["is_guest"] is False

    # Aynı e-posta ikinci kez kayıt olamaz
    assert _register(client).status_code == 409

    # Doğru şifreyle giriş → yeni token
    r = client.post(
        "/users/login", json={"email": "cizer@example.com", "password": "cokgizli123"}
    )
    assert r.status_code == 200
    token = r.json()["token"]
    assert client.get("/profile", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    # Yanlış şifre reddedilir
    r = client.post(
        "/users/login", json={"email": "cizer@example.com", "password": "yanlis1234"}
    )
    assert r.status_code == 401


def test_short_password_rejected(client):
    assert _register(client, password="kisa").status_code == 422


def test_guest_upgrade_keeps_progress(client):
    headers = _guest(client)
    # Misafirken bir ders tamamla
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 200

    # Hesaba yükselt
    r = client.post(
        "/users/upgrade",
        json={"email": "misafir@example.com", "password": "cokgizli123"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["is_guest"] is False

    # Aynı token ile ilerleme duruyor
    profile = client.get("/profile", headers=headers).json()
    assert len(profile["gelisim_macerasi"]) == 1

    # Tekrar yükseltme reddedilir
    r = client.post(
        "/users/upgrade",
        json={"email": "baska@example.com", "password": "cokgizli123"},
        headers=headers,
    )
    assert r.status_code == 409


def test_image_privacy(client):
    owner = _guest(client)
    stranger = _guest(client)

    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=owner
    )
    sid = r.json()["submission_id"]

    # Sahibi görebilir
    r = client.get(f"/submissions/{sid}/image", headers=owner)
    assert r.status_code == 200
    assert r.content == PNG

    # Yabancı, özel gönderiyi göremez
    assert client.get(f"/submissions/{sid}/image", headers=stranger).status_code == 404

    # Herkese açık yapılınca görebilir
    client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner)
    assert client.get(f"/submissions/{sid}/image", headers=stranger).status_code == 200


def test_ai_failure_returns_503(client, monkeypatch):
    """Sağlayıcı çökerse kullanıcı 500 değil, anlaşılır 503 mesajı almalı."""

    class FailingProvider:
        async def redline_analysis(self, image, lesson_context):
            raise RuntimeError("simüle edilmiş sağlayıcı hatası")

        async def assess_level(self, images):
            raise RuntimeError("simüle edilmiş sağlayıcı hatası")

    import app.api.onboarding as onboarding_module
    import app.api.tree as tree_module

    monkeypatch.setattr(tree_module, "get_ai_provider", lambda: FailingProvider())
    monkeypatch.setattr(onboarding_module, "get_ai_provider", lambda: FailingProvider())

    headers = _guest(client)
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 503
    assert "AI şu an yanıt veremiyor" in r.json()["detail"]

    r = client.post(
        "/onboarding/assess",
        files=[("files", (f"c{i}.png", io.BytesIO(PNG), "image/png")) for i in range(3)],
        headers=headers,
    )
    assert r.status_code == 503
