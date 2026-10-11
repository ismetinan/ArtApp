"""Topluluk beğenileri (2026-10): anonim, sayı odaklı, en çok beğenilen üstte."""

import json

from tests.test_mentors import _submit, _user


def _share(client, h):
    sid = _submit(client, h)
    r = client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h)
    assert r.status_code == 200
    return sid


def _feed(client, h):
    return client.get("/gallery", headers=h).json()["items"]


def test_like_unlike_idempotent_and_counts(client):
    owner, _ = _user(client, "Sahip")
    fan, _ = _user(client, "Hayran")
    sid = _share(client, owner)

    r = client.put(f"/submissions/{sid}/like", headers=fan)
    assert r.json() == {"like_count": 1, "liked_by_me": True}
    # İkinci beğeni sayıyı artırmaz
    assert client.put(f"/submissions/{sid}/like", headers=fan).json()["like_count"] == 1
    item = _feed(client, fan)[0]
    assert item["like_count"] == 1 and item["liked_by_me"] is True
    assert _feed(client, owner)[0]["liked_by_me"] is False

    r = client.delete(f"/submissions/{sid}/like", headers=fan)
    assert r.json() == {"like_count": 0, "liked_by_me": False}
    assert client.delete(f"/submissions/{sid}/like", headers=fan).status_code == 200


def test_most_liked_first_then_newest(client):
    a, _ = _user(client, "A")
    b, _ = _user(client, "B")
    old = _share(client, a)
    popular = _share(client, a)
    newest = _share(client, a)
    for i in range(3):
        fan, _ = _user(client, f"Fan{i}")
        client.put(f"/submissions/{popular}/like", headers=fan)
    client.put(f"/submissions/{old}/like", headers=b)
    order = [i["submission_id"] for i in _feed(client, b)]
    assert order == [popular, old, newest]


def test_cannot_like_own_private_or_hidden(client):
    owner, _ = _user(client, "Sahip")
    fan, _ = _user(client, "Hayran")
    sid = _share(client, owner)
    assert client.put(f"/submissions/{sid}/like", headers=owner).status_code == 403
    private = _submit(client, owner)
    assert client.put(f"/submissions/{private}/like", headers=fan).status_code == 404
    assert client.put("/submissions/99999/like", headers=fan).status_code == 404


def test_likes_are_anonymous(client):
    owner, _ = _user(client, "Sahip")
    fan, _ = _user(client, "GizliHayranAdı")
    sid = _share(client, owner)
    client.put(f"/submissions/{sid}/like", headers=fan)
    body = json.dumps(_feed(client, owner)) + json.dumps(
        client.put(f"/submissions/{sid}/like", headers=fan).json()
    )
    assert "GizliHayranAdı" not in body


def test_cannot_like_demo_content_as_real_user(client):
    r = client.post("/users/register", json={
        "email": "demo@artora.app", "password": "GucluParola123!", "display_name": "Demo"})
    demo = {"Authorization": f"Bearer {r.json()['token']}"}
    sid = _share(client, demo)
    real, _ = _user(client, "Gerçek")
    assert client.put(f"/submissions/{sid}/like", headers=real).status_code == 404


def test_account_deletion_with_likes(client):
    owner, _ = _user(client, "Sahip")
    fan, _ = _user(client, "Hayran")
    sid = _share(client, owner)
    mine = _share(client, fan)
    client.put(f"/submissions/{sid}/like", headers=fan)
    client.put(f"/submissions/{mine}/like", headers=owner)
    # Hem verdiği hem aldığı beğeniler FK'yi bozmamalı
    assert client.delete("/users/me", headers=fan).status_code == 200
    assert _feed(client, owner)[0]["like_count"] == 0
