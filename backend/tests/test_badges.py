"""Rozetler + çıkış kampanyası (2026-09).

Para/güven akışı (CLAUDE.md §6): kampanya jetonu hesap başına TEK kez,
yalnız kayıtlı hesaba, yalnız kampanya süresince verilir.
"""

from datetime import datetime, timedelta, timezone

import pytest

from tests.test_mentors import _submit, _user


@pytest.fixture
def campaign(monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(
        s, "launch_campaign_until", datetime.now(timezone.utc).date() + timedelta(days=5)
    )
    monkeypatch.setattr(s, "launch_bonus_jetons", 10)
    return s


def _register(client, email="kurucu@example.com"):
    r = client.post(
        "/users/register",
        json={"email": email, "password": "GucluParola123!", "display_name": "Kurucu"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _codes(badges):
    return [b["code"] for b in badges]


def _bonus_rows(client, h):
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import JetonTransaction

    me = client.get("/profile", headers=h).json()["id"]
    with db_module.SessionLocal() as s:
        return s.execute(
            select(JetonTransaction).where(
                JetonTransaction.user_id == me, JetonTransaction.reason == "launch_bonus"
            )
        ).scalars().all()


def test_no_campaign_by_default(client):
    h = _register(client)
    p = client.get("/profile", headers=h).json()
    assert p["launch_campaign"] is None
    assert p["launch_bonus_granted"] == 0
    assert "founding_artist" not in _codes(p["badges"])


def test_registered_user_gets_badge_and_bonus_once(client, campaign):
    h = _register(client)
    p = client.get("/profile", headers=h).json()
    assert p["launch_bonus_granted"] == 10
    assert _codes(p["new_badges"]) == ["founding_artist"]
    assert p["new_badges"][0]["title"] == "Kurucu Çizer"
    balance = p["jeton_balance"]

    # İkinci açılış: ne rozet ne jeton tekrar verilir
    p2 = client.get("/profile", headers=h).json()
    assert p2["launch_bonus_granted"] == 0 and p2["new_badges"] == []
    assert p2["jeton_balance"] == balance
    assert _codes(p2["badges"]) == ["founding_artist"]
    assert len(_bonus_rows(client, h)) == 1
    # Kampanya jetonu ücretsizdir — altın (satın alınmış) sayılmaz
    assert p2["gold_jeton_balance"] == 0


def test_guest_gets_badge_then_bonus_after_upgrade(client, campaign):
    h, _ = _user(client, "Misafir")
    p = client.get("/profile", headers=h).json()
    assert _codes(p["new_badges"]) == ["founding_artist"]
    assert p["launch_bonus_granted"] == 0
    assert p["launch_campaign"]["bonus_jetons"] == 10  # "hesap oluştur" teşviki

    r = client.post(
        "/users/upgrade",
        json={"email": "donusen@example.com", "password": "GucluParola123!"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    h2 = {"Authorization": f"Bearer {r.json()['token']}"}
    p2 = client.get("/profile", headers=h2).json()
    assert p2["launch_bonus_granted"] == 10
    assert p2["new_badges"] == []  # rozet zaten vardı


def test_campaign_over_grants_nothing(client, campaign, monkeypatch):
    monkeypatch.setattr(
        campaign, "launch_campaign_until", datetime.now(timezone.utc).date() - timedelta(days=1)
    )
    h = _register(client)
    p = client.get("/profile", headers=h).json()
    assert p["launch_campaign"] is None and p["launch_bonus_granted"] == 0
    assert "founding_artist" not in _codes(p["badges"])


def test_progress_badges(client):
    h, _ = _user(client, "Öğrenci")
    assert client.get("/profile", headers=h).json()["badges"] == []
    _submit(client, h)
    p = client.get("/profile", headers=h).json()
    assert "first_lesson" in _codes(p["new_badges"])
    assert client.get("/profile", headers=h).json()["new_badges"] == []


def test_streak_badge(client):
    from app import db as db_module
    from app.models.tables import UserActivityDay

    h, data = _user(client, "Seri")
    client.get("/profile", headers=h)  # bugünü kaydeder
    today = datetime.now(timezone.utc).date()
    with db_module.SessionLocal() as s:
        for i in range(1, 7):
            s.add(UserActivityDay(user_id=data["id"], day=today - timedelta(days=i)))
        s.commit()
    assert "streak_7" in _codes(client.get("/profile", headers=h).json()["new_badges"])


def test_streak_broken_no_badge(client):
    from app import db as db_module
    from app.models.tables import UserActivityDay

    h, data = _user(client, "Kesik")
    client.get("/profile", headers=h)
    today = datetime.now(timezone.utc).date()
    with db_module.SessionLocal() as s:
        for i in (1, 2, 4, 5, 6, 7):  # 3 gün önce boşluk
            s.add(UserActivityDay(user_id=data["id"], day=today - timedelta(days=i)))
        s.commit()
    assert "streak_7" not in _codes(client.get("/profile", headers=h).json()["badges"])


def test_badges_localized_english(client, campaign):
    h = _register(client, "en@example.com")
    client.patch("/users/me/language", json={"language": "en"}, headers=h)
    p = client.get("/profile", headers=h).json()
    assert p["badges"][0]["title"] == "Founding Artist"


def test_delete_account_with_badges(client, campaign):
    h = _register(client, "sil@example.com")
    client.get("/profile", headers=h)
    assert client.delete("/users/me", headers=h).status_code == 200

