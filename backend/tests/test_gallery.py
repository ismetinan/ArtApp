"""Topluluk galerisi: yalnız herkese açık gönderiler, en yeni önce, is_mine bayrağı."""

from tests.test_mentors import _submit, _user


def test_gallery_lists_only_public(client):
    owner_h, _ = _user(client, "Paylaşımcı")
    sid_public = _submit(client, owner_h)  # cizgi-temelleri
    sid_private = _submit(client, owner_h, node="jest-cizimi")

    # Varsayılan özel → galeri boş
    viewer_h, _ = _user(client, "İzleyici")
    assert client.get("/gallery", headers=viewer_h).json()["items"] == []

    # Biri herkese açık yapılınca yalnız o görünür
    r = client.patch(
        f"/submissions/{sid_public}/privacy", json={"is_public": True}, headers=owner_h
    )
    assert r.status_code == 200
    items = client.get("/gallery", headers=viewer_h).json()["items"]
    assert [i["submission_id"] for i in items] == [sid_public]
    item = items[0]
    assert item["display_name"] == "Paylaşımcı"
    assert item["node_title"] == "Çizgi Temelleri"
    assert item["is_mine"] is False

    # Sahibi kendi kaydını is_mine=True görür
    mine = client.get("/gallery", headers=owner_h).json()["items"][0]
    assert mine["is_mine"] is True

    # Görsel: paylaşan dışındaki kullanıcı da açık görseli çekebilir,
    # özel olan (sid_private) 404 kalır
    assert (
        client.get(f"/submissions/{sid_public}/image", headers=viewer_h).status_code
        == 200
    )
    assert (
        client.get(f"/submissions/{sid_private}/image", headers=viewer_h).status_code
        == 404
    )


def test_share_requires_min_level(client, monkeypatch):
    """Seviye kapısı: eşiğin altındaki kullanıcı herkese açamaz (403);
    seviyesi yeten açabilir. Özele çekmek her seviyede serbest."""
    from sqlalchemy import select

    from app import db as db_module
    from app.core.config import get_settings
    from app.models.tables import User

    monkeypatch.setattr(get_settings(), "community_share_min_level", 3)

    owner_h, _ = _user(client, "Yeni Çizer")
    owner_id = client.get("/profile", headers=owner_h).json()["id"]
    sid = _submit(client, owner_h)

    # Seviye 1 (misafir varsayılanı) → paylaşım kilitli
    r = client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h
    )
    assert r.status_code == 403
    viewer_h, _ = _user(client, "İzleyici")
    assert client.get("/gallery", headers=viewer_h).json()["items"] == []

    # Seviyeyi 3'e çıkar → artık paylaşabilir
    with db_module.SessionLocal() as s:
        u = s.execute(select(User).where(User.id == owner_id)).scalar_one()
        u.level = 3
        s.commit()
    r = client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h
    )
    assert r.status_code == 200 and r.json()["is_public"] is True
    items = client.get("/gallery", headers=viewer_h).json()["items"]
    assert [i["submission_id"] for i in items] == [sid]

    # Özele çekmek seviye kapısına takılmaz
    r = client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": False}, headers=owner_h
    )
    assert r.status_code == 200 and r.json()["is_public"] is False


def test_gallery_pagination_newest_first(client):
    owner_h, _ = _user(client, "Üretken")
    ids = []
    for node in ("cizgi-temelleri", "jest-cizimi"):
        sid = _submit(client, owner_h, node=node)
        client.patch(
            f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h
        )
        ids.append(sid)

    items = client.get("/gallery?limit=1", headers=owner_h).json()["items"]
    assert len(items) == 1 and items[0]["submission_id"] == ids[-1]  # en yeni önce
    items2 = client.get("/gallery?limit=1&offset=1", headers=owner_h).json()["items"]
    assert items2[0]["submission_id"] == ids[0]
