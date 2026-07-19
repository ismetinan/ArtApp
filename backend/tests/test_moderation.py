"""UGC moderasyonu: şikayet, admin hide/dismiss, yeniden paylaşım engeli."""

from tests.test_mentors import _make_admin, _submit, _user


def _public_submission(client):
    owner_h, owner = _user(client, "İçerik Sahibi")
    sid = _submit(client, owner_h)
    client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h)
    return owner_h, sid


def test_report_dedupe_and_404_for_private(client):
    owner_h, sid = _public_submission(client)
    viewer_h, _ = _user(client, "Şikayetçi")

    assert (
        client.post(f"/submissions/{sid}/report", json={"reason": "spam"}, headers=viewer_h)
        .status_code
        == 200
    )
    # Aynı kullanıcı ikinci kez → yine 200, tek kayıt
    client.post(f"/submissions/{sid}/report", json={"reason": "uygunsuz"}, headers=viewer_h)

    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import ContentReport

    with db_module.SessionLocal() as s:
        assert len(s.execute(select(ContentReport)).scalars().all()) == 1

    # Özel gönderi şikayet edilemez (varlığı sızdırılmaz)
    private_sid = _submit(client, owner_h, node="jest-cizimi")
    r = client.post(f"/submissions/{private_sid}/report", json={}, headers=viewer_h)
    assert r.status_code == 404


def test_admin_hide_removes_and_blocks_republish(client):
    owner_h, sid = _public_submission(client)
    viewer_h, _ = _user(client, "Raporcu")
    client.post(f"/submissions/{sid}/report", json={"reason": "telif"}, headers=viewer_h)

    admin_h, _ = _user(client, "Moderatör")
    _make_admin(client, admin_h)

    reports = client.get("/admin/reports", headers=admin_h).json()["reports"]
    assert len(reports) == 1
    assert reports[0]["submission_id"] == sid
    assert reports[0]["report_count"] == 1 and reports[0]["reasons"] == ["telif"]

    r = client.post(f"/admin/reports/{sid}/hide", headers=admin_h)
    assert r.status_code == 200
    # Galeriden düştü, şikayet listesi boşaldı
    assert client.get("/gallery", headers=viewer_h).json()["items"] == []
    assert client.get("/admin/reports", headers=admin_h).json()["reports"] == []
    # Sahibi yeniden herkese açık YAPAMAZ (403 + yerelleştirilmiş mesaj)
    r = client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h
    )
    assert r.status_code == 403


def test_admin_dismiss_keeps_content(client):
    _, sid = _public_submission(client)
    viewer_h, _ = _user(client, "Hassas")
    client.post(f"/submissions/{sid}/report", json={"reason": "diger"}, headers=viewer_h)

    admin_h, _ = _user(client, "Hoşgörülü Mod")
    _make_admin(client, admin_h)
    client.post(f"/admin/reports/{sid}/dismiss", headers=admin_h)

    # İçerik galeride kalır, şikayetler temizlenir
    items = client.get("/gallery", headers=viewer_h).json()["items"]
    assert [i["submission_id"] for i in items] == [sid]
    assert client.get("/admin/reports", headers=admin_h).json()["reports"] == []

    # Admin olmayan moderasyon uçlarına giremez
    assert client.get("/admin/reports", headers=viewer_h).status_code == 403
    assert client.post(f"/admin/reports/{sid}/hide", headers=viewer_h).status_code == 403
