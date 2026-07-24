"""Faz 3 dilim 1: seçmeli mentorluk (3 ALTIN jeton) + mentor arama/sıralama.

Faz 4 (gelir paylaşımı) sonrası: seçmeli mentor yalnız altın (gelir-destekli)
jetonla — ücretsiz hoşgeldin jetonu seçmeli mentoru satın alamaz.
"""

from tests.test_billing import _enable_billing, _mock_play
from tests.test_mentors import _approved_mentor, _enable_market, _submit, _user


def _mentor_profile_id(client, headers):
    return client.get("/mentors", headers=headers).json()["mentors"][0]["id"]


def _buy_gold(client, headers, token="dm-gold"):
    """5 altın jeton satın alır (3 ücretsiz + 5 altın = 8 toplam)."""
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_5", "purchase_token": token},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_direct_request_costs_three_gold(client, monkeypatch):
    _enable_market(monkeypatch)
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Seçici Öğrenci")
    _buy_gold(client, student_h)  # 3 ücretsiz + 5 altın
    sid = _submit(client, student_h)
    pid = _mentor_profile_id(client, student_h)

    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    )
    assert r.status_code == 200, r.text
    assert r.json()["jeton_balance"] == 5  # 8 - 3 altın
    assert r.json()["mentor_display_name"] == "Mentor"
    # altın bakiye 5 → 2
    assert client.get("/billing/status", headers=student_h).json()["gold_jeton_balance"] == 2


def test_free_jetons_cannot_buy_direct(client, monkeypatch):
    _enable_market(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Ücretsizci")
    sid = _submit(client, student_h)
    pid = _mentor_profile_id(client, student_h)
    # yalnız 3 ücretsiz jeton var → seçmeli 402 (altın gerekli), jeton harcanmaz
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    )
    assert r.status_code == 402
    assert "altın" in r.json()["detail"]  # gold_insufficient (tr)
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 3


def test_direct_request_insufficient_jetons(client, monkeypatch):
    _enable_market(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Az Jetonlu")
    pid = _mentor_profile_id(client, student_h)

    # 1 jeton havuza harcandı → 2 kaldı → seçmeli (3) reddedilir
    sid1 = _submit(client, student_h, node="cizgi-temelleri")
    assert (
        client.post(f"/submissions/{sid1}/mentor-request", headers=student_h).status_code
        == 200
    )
    sid2 = _submit(client, student_h, node="sekil-ve-form")
    r = client.post(
        f"/submissions/{sid2}/mentor-request", json={"mentor_id": pid}, headers=student_h
    )
    assert r.status_code == 402
    assert "3" in r.json()["detail"]  # maliyet mesajda geçer
    profile = client.get("/profile", headers=student_h).json()
    assert profile["jeton_balance"] == 2  # hiçbir şey harcanmadı


def test_direct_request_unavailable_mentor(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Şanssız")
    sid = _submit(client, student_h)
    pid = _mentor_profile_id(client, student_h)

    # mentor müsaitliği kapatır → seçmeli istek 409, jeton harcanmaz
    client.patch("/mentor/me", json={"is_available": False}, headers=mentor_h)
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    )
    assert r.status_code == 409
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 3

    # var olmayan profil → 404
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": 9999}, headers=student_h
    )
    assert r.status_code == 404


def test_direct_request_to_self_blocked(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    sid = _submit(client, mentor_h)
    pid = _mentor_profile_id(client, mentor_h)
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=mentor_h
    )
    assert r.status_code == 409


def test_direct_request_timeout_refunds_three_gold(client, monkeypatch):
    from datetime import datetime, timedelta, timezone

    _enable_market(monkeypatch)
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Bekleyen Seçici")
    _buy_gold(client, student_h, token="to-gold")  # 3 ücretsiz + 5 altın
    sid = _submit(client, student_h)
    pid = _mentor_profile_id(client, student_h)
    client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    )
    # 3 altın harcandı → toplam 5, altın 2
    p = client.get("/billing/status", headers=student_h).json()
    assert p["jeton_balance"] == 5 and p["gold_jeton_balance"] == 2

    from app import db as db_module
    from app.models.tables import MentorshipRequest

    with db_module.SessionLocal() as s:
        r = s.query(MentorshipRequest).one()
        assert r.jeton_cost == 3 and r.paid_cost == 3
        r.assigned_at = datetime.now(timezone.utc) - timedelta(hours=49)
        s.commit()

    client.get("/mentor-requests", headers=student_h)
    # iade altın bileşimini de geri yükler → toplam 8, altın 5
    p = client.get("/billing/status", headers=student_h).json()
    assert p["jeton_balance"] == 8 and p["gold_jeton_balance"] == 5


def test_mentor_search_and_sort(client, monkeypatch):
    _enable_market(monkeypatch)
    _approved_mentor(client, monkeypatch)  # "Mentor", bio "10 yıl çizerim"
    student_h, _ = _user(client, "Arayan")

    # ada göre bul
    r = client.get("/mentors?q=mento", headers=student_h).json()["mentors"]
    assert len(r) == 1
    # bio'ya göre bul
    r = client.get("/mentors?q=çizerim", headers=student_h).json()["mentors"]
    assert len(r) == 1
    # eşleşmeyen arama boş döner
    r = client.get("/mentors?q=yokböylebiri", headers=student_h).json()["mentors"]
    assert r == []
