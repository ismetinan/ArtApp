"""Önleyici içerik filtresi: paylaşım/portfolyo/mentor isteği anında AI kontrolü.

Mock sağlayıcı, içeriğinde b"NSFW" geçen görselleri güvensiz sayar.
"""

import io

from tests.test_mentors import PNG, _approved_mentor, _enable_market, _submit, _user

# PNG başlığı korunur, sonuna NSFW işareti eklenir — mock bunu güvensiz sayar
NSFW_PNG = PNG + b"NSFW"


def _submit_bytes(client, headers, content, node="cizgi-temelleri"):
    r = client.post(
        f"/skill-tree/{node}/submit",
        files={"file": ("odev.png", io.BytesIO(content), "image/png")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["submission_id"]


def test_unsafe_image_cannot_go_public(client):
    h, _ = _user(client, "Densiz")
    sid = _submit_bytes(client, h, NSFW_PNG)

    r = client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h)
    assert r.status_code == 422
    assert "kural" in r.json()["detail"]  # yerelleştirilmiş, suçlayıcı olmayan mesaj

    # Galeriye asla düşmedi; ikinci deneme de (önbellekten) reddedilir
    assert client.get("/gallery", headers=h).json()["items"] == []
    r = client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h)
    assert r.status_code == 422

    from app import db as db_module
    from app.models.tables import Submission

    with db_module.SessionLocal() as s:
        assert s.get(Submission, sid).moderation_status == "unsafe"


def test_safe_image_goes_public_and_caches_verdict(client):
    h, _ = _user(client, "Temiz")
    sid = _submit_bytes(client, h, PNG)
    r = client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h)
    assert r.status_code == 200

    from app import db as db_module
    from app.models.tables import Submission

    with db_module.SessionLocal() as s:
        assert s.get(Submission, sid).moderation_status == "safe"
    # Görünürlüğü kapatıp açmak yeniden AI çağrısı gerektirmez (safe önbellek)
    client.patch(f"/submissions/{sid}/privacy", json={"is_public": False}, headers=h)
    assert (
        client.patch(
            f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h
        ).status_code
        == 200
    )


def test_unsafe_blocks_mentor_request_and_portfolio(client, monkeypatch):
    _enable_market(monkeypatch)
    _approved_mentor(client, monkeypatch)

    h, _ = _user(client, "Sınırda")
    sid = _submit_bytes(client, h, NSFW_PNG)

    # Mentora gönderilemez — jeton da harcanmaz
    r = client.post(f"/submissions/{sid}/mentor-request", headers=h)
    assert r.status_code == 422
    assert client.get("/profile", headers=h).json()["jeton_balance"] == 3

    # Portfolyoda kullanılamaz
    r = client.post(
        "/mentors/apply",
        json={"bio": "x", "styles": ["manga"], "portfolio_submission_ids": [sid]},
        headers=h,
    )
    assert r.status_code == 422

    # Temiz görselle akış normal işler
    clean_sid = _submit_bytes(client, h, PNG, node="jest-cizimi")
    assert (
        client.post(f"/submissions/{clean_sid}/mentor-request", headers=h).status_code
        == 200
    )
