"""Beta sağlık panosu: /admin/stats sayımları ve yetki."""

from tests.test_mentors import _make_admin, _submit, _user


def test_stats_counts_and_permissions(client):
    h, _ = _user(client, "İstatistikçi")
    # Admin olmayan 403
    assert client.get("/admin/stats", headers=h).status_code == 403

    _make_admin(client, h)
    _submit(client, h)  # 1 assignment (hoşgeldin 3 jeton, harcama yok)
    client.post("/waitlist", json={"email": "stat@example.com", "language": "tr"})

    s = client.get("/admin/stats", headers=h).json()
    assert s["users_total"] >= 1 and s["users_last_7d"] >= 1
    assert s["submissions_by_kind"].get("assignment") == 1
    assert s["submissions_last_7d"] == 1
    assert s["jetons_spent_total"] == 0
    assert s["purchases_total"] == 0
    assert s["waitlist_total"] == 1
    assert s["mentor_requests_by_status"] == {}
