"""Admin analitiği (2026-09): aktiflik kaydı, olaylar, anonimlik, yetki.

Gizlilik burada test edilen asıl sözleşme: analitik yanıtlarında e-posta,
görünen ad ya da dosya yolu ASLA bulunmamalı.
"""

import json
from datetime import date, datetime, timedelta, timezone

from tests.test_analysis_jobs import _submit_async
from tests.test_mentors import _make_admin, _submit, _user

ENDPOINTS = ("overview", "funnel", "retention", "lessons", "economy", "users")


def _admin(client):
    h, _ = _user(client, "Yönetici")
    _make_admin(client, h)
    return h


def test_analytics_requires_admin(client):
    h, _ = _user(client, "Meraklı")
    for ep in ENDPOINTS:
        assert client.get(f"/admin/analytics/{ep}", headers=h).status_code == 403


def test_activity_recorded_once_per_day_with_platform(client):
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import User, UserActivityDay

    h, data = _user(client, "Aktif")
    hdr = {**h, "X-Platform": "iOS", "X-App-Version": "0.10.0+24"}
    for _ in range(3):
        client.get("/profile", headers=hdr)
    with db_module.SessionLocal() as s:
        days = s.execute(
            select(UserActivityDay).where(UserActivityDay.user_id == data["id"])
        ).scalars().all()
        u = s.get(User, data["id"])
        assert len(days) == 1
        assert u.platform == "ios" and u.app_version == "0.10.0+24"
        assert u.last_seen_at is not None


def test_activity_rejects_junk_headers(client):
    from app import db as db_module
    from app.models.tables import User

    h, data = _user(client, "Garip")
    client.get(
        "/profile",
        headers={**h, "X-Platform": "<script>", "X-App-Version": "1.0; DROP TABLE"},
    )
    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        assert u.platform is None and u.app_version is None


def test_events_whitelist_and_props_cleaning(client):
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import AppEvent

    h, _ = _user(client, "Olaycı")
    r = client.post("/events", json={"name": "hack_me"}, headers=h)
    assert r.status_code == 422
    r = client.post(
        "/events",
        json={"name": "lesson_opened",
              "props": {"node_id": "cizgi-temelleri", "email": "x@y.z"}},
        headers=h,
    )
    assert r.status_code == 204
    assert client.post("/events", json={"name": "lesson_opened"}).status_code == 401
    with db_module.SessionLocal() as s:
        ev = s.execute(select(AppEvent)).scalar_one()
        assert ev.props == {"node_id": "cizgi-temelleri"}  # bilinmeyen anahtar atıldı


def test_events_user_rate_limit(client, monkeypatch):
    from app.core import ratelimit
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    ratelimit._BUCKETS.clear()
    h, _ = _user(client, "Spamcı")
    codes = [
        client.post("/events", json={"name": "store_opened"}, headers=h).status_code
        for _ in range(61)
    ]
    assert codes[:60] == [204] * 60 and codes[60] == 429
    ratelimit._BUCKETS.clear()


def test_overview_funnel_lessons_and_anonymity(client):
    admin = _admin(client)
    h, data = _user(client, "Gizli İsim Soyisim")
    client.get("/profile", headers={**h, "X-Platform": "android"})
    client.post("/skill-tree/cizgi-temelleri/assignment", headers=h)
    client.post(
        "/events", json={"name": "lesson_opened", "props": {"node_id": "cizgi-temelleri"}},
        headers=h,
    )
    _submit(client, h)

    ov = client.get("/admin/analytics/overview", headers=admin).json()
    # Admin sayılmaz → yalnız 1 gerçek kullanıcı
    assert ov["users_total"] == 1 and ov["users_guest"] == 1
    assert ov["dau"] == 1 and ov["mau"] == 1
    assert ov["platforms"] == {"android": 1}
    assert len(ov["series_30d"]) == 30 and ov["series_30d"][-1]["signups"] == 1

    steps = {
        s["key"]: s["users"]
        for s in client.get("/admin/analytics/funnel", headers=admin).json()["steps"]
    }
    assert steps["signed_up"] == 1
    assert steps["lesson_opened"] == 1
    assert steps["assignment_generated"] == 1
    assert steps["assignment_submitted"] == 1
    assert steps["lesson_completed"] == 1
    assert steps["onboarded"] == 0

    lessons = client.get("/admin/analytics/lessons", headers=admin).json()["lessons"]
    row = next(r for r in lessons if r["node_id"] == "cizgi-temelleri")
    assert row["opened"] == 1 and row["submitters"] == 1 and row["completed"] == 1

    users = client.get("/admin/analytics/users", headers=admin).json()
    assert users["total"] == 1
    assert users["users"][0]["id"] == data["id"]
    assert users["users"][0]["lessons_completed"] == 1

    # Hiçbir analitik yanıtında kimlik/içerik sızmamalı
    for ep in ENDPOINTS:
        body = json.dumps(client.get(f"/admin/analytics/{ep}", headers=admin).json())
        assert "Gizli İsim" not in body and "Gizli \\u0130sim" not in body
        assert "@" not in body and "storage" not in body and ".png" not in body


def test_retention_cohorts(client):
    from app import db as db_module
    from app.models.tables import User, UserActivityDay

    admin = _admin(client)
    h, data = _user(client, "Kohort")
    today = datetime.now(timezone.utc).date()
    signup = today - timedelta(days=30)
    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        u.created_at = datetime.combine(signup, datetime.min.time(), timezone.utc)
        s.add(UserActivityDay(user_id=u.id, day=signup + timedelta(days=3)))  # w1
        s.commit()

    cohorts = client.get("/admin/analytics/retention", headers=admin).json()["cohorts"]
    row = next(c for c in cohorts if c["size"] == 1)
    assert row["w1"] == 1.0 and row["w2"] == 0.0


def test_economy_counts_ai_jobs(client):
    admin = _admin(client)
    h, _ = _user(client, "Analizci")
    assert _submit_async(client, h).status_code == 200
    eco = client.get("/admin/analytics/economy", headers=admin).json()
    assert eco["ai_jobs_30d"]["by_status"] == {"done": 1}
    assert eco["ai_jobs_30d"]["fail_rate"] == 0


def test_delete_account_after_async_analysis(client):
    """Regresyon: AnalysisJob/Assignment/AbilityHistory satırları hesap silmeyi
    FK ihlaliyle 500'e düşürüyordu (SQLite FK'yi zorlamadığı için gizliydi)."""
    h, _ = _user(client, "Silinecek")
    client.post("/skill-tree/cizgi-temelleri/assignment", headers=h)
    assert _submit_async(client, h).status_code == 200
    client.post("/events", json={"name": "store_opened"}, headers=h)
    r = client.delete("/users/me", headers=h)
    assert r.status_code == 200, r.text
