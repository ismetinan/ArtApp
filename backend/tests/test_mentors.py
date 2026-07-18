"""Faz 2 mentor pazarı: jeton ekonomisi, havuz eşleştirme, yetki ve tam akış.

Para/güven akışı (CLAUDE.md §6) — her dal ayrı test edilir. Flag testler içinde
cached settings örneği üzerinden açılır (varsayılan: kapalı).
"""

import io
from datetime import datetime, timedelta, timezone

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _enable_market(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "mentor_market_enabled", True)


def _user(client, name):
    r = client.post("/users/guest", json={"display_name": name})
    assert r.status_code == 200
    data = r.json()
    return {"Authorization": f"Bearer {data['token']}"}, data


def _submit(client, headers, node="cizgi-temelleri"):
    r = client.post(
        f"/skill-tree/{node}/submit",
        files={"file": ("odev.png", io.BytesIO(PNG), "image/png")},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["submission_id"]


def _make_admin(client, headers):
    """Test DB'sinde admin bayrağını doğrudan basar (prod'da SQL ile yapılır)."""
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import User

    me = client.get("/profile", headers=headers).json()
    with db_module.SessionLocal() as s:
        u = s.execute(select(User).where(User.id == me["id"])).scalar_one()
        u.is_admin = True
        s.commit()


def _approved_mentor(client, monkeypatch, name="Mentor"):
    """Başvuru + admin onayıyla hazır mentor döner (headers)."""
    mentor_h, _ = _user(client, name)
    r = client.post(
        "/mentors/apply", json={"bio": "10 yıl çizerim", "styles": ["manga"]},
        headers=mentor_h,
    )
    assert r.status_code == 200
    admin_h, _ = _user(client, "Admin")
    _make_admin(client, admin_h)
    apps = client.get("/admin/mentor-applications", headers=admin_h).json()["applications"]
    r = client.post(
        f"/admin/mentor-applications/{apps[0]['id']}/approve", headers=admin_h
    )
    assert r.json()["status"] == "approved"
    return mentor_h


def test_flag_off_hides_endpoints(client):
    h, _ = _user(client, "X")
    assert client.get("/mentors", headers=h).status_code == 404
    assert client.post("/mentors/apply", json={}, headers=h).status_code == 404


def test_welcome_jetons_on_signup(client):
    _, data = _user(client, "Yeni")
    h = {"Authorization": f"Bearer {data['token']}"}
    assert client.get("/profile", headers=h).json()["jeton_balance"] == 3


def test_full_flow_request_feedback_rating(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Öğrenci")
    sid = _submit(client, student_h)

    # istek: 1 jeton düşer, mentora atanır
    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 200, r.text
    req = r.json()
    assert req["jeton_balance"] == 2
    assert req["mentor_display_name"] == "Mentor"

    # aynı ödev için ikinci istek engellenir
    assert (
        client.post(f"/submissions/{sid}/mentor-request", headers=student_h).status_code
        == 409
    )

    # mentor kuyruğunda görünür, AI analizi bağlamıyla
    queue = client.get("/mentor/queue", headers=mentor_h).json()["requests"]
    assert len(queue) == 1 and queue[0]["ai_result"] is not None

    # cevaplanmadan rating verilemez
    assert (
        client.post(
            f"/mentor-requests/{req['request_id']}/rating",
            json={"rating": 5},
            headers=student_h,
        ).status_code
        == 409
    )

    # feedback: boş metin reddedilir, dolu metin answered yapar
    fb = f"/mentor-requests/{req['request_id']}/feedback"
    assert client.post(fb, json={"feedback_text": "  "}, headers=mentor_h).status_code == 422
    assert (
        client.post(fb, json={"feedback_text": "Eline sağlık, omuz açısına dikkat."},
                    headers=mentor_h).status_code
        == 200
    )

    # öğrenci görür + puanlar (bir kez)
    mine = client.get("/mentor-requests", headers=student_h).json()["requests"]
    assert mine[0]["status"] == "answered" and "omuz" in mine[0]["feedback_text"]
    rate = f"/mentor-requests/{req['request_id']}/rating"
    assert client.post(rate, json={"rating": 5}, headers=student_h).status_code == 200
    assert client.post(rate, json={"rating": 4}, headers=student_h).status_code == 409

    # rating mentor listesine yansır
    mentors = client.get("/mentors", headers=student_h).json()["mentors"]
    assert mentors[0]["rating"] == 5.0 and mentors[0]["answered_count"] == 1


def test_insufficient_jetons(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Fakir Öğrenci")
    # 3 jetonu 3 istekle bitir (farklı ödevler)
    for node in ("cizgi-temelleri", "sekil-ve-form", "jest-cizimi"):
        sid = _submit(client, student_h, node=node)
        assert (
            client.post(f"/submissions/{sid}/mentor-request", headers=student_h).status_code
            == 200
        )
    sid = _submit(client, student_h, node="temel-oranlar")
    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 402
    profile = client.get("/profile", headers=student_h).json()
    assert profile["jeton_balance"] == 0  # asla negatif olmaz


def test_no_mentor_available_spends_nothing(client, monkeypatch):
    _enable_market(monkeypatch)
    student_h, _ = _user(client, "Yalnız Öğrenci")
    sid = _submit(client, student_h)
    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 409
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 3


def test_mentor_not_assigned_to_own_submission(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    # tek mentor kendisi → kendi ödevine istek atınca müsait mentor yok
    sid = _submit(client, mentor_h)
    assert (
        client.post(f"/submissions/{sid}/mentor-request", headers=mentor_h).status_code
        == 409
    )


def test_timeout_refunds_jeton(client, monkeypatch):
    _enable_market(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Sabırlı Öğrenci")
    sid = _submit(client, student_h)
    assert (
        client.post(f"/submissions/{sid}/mentor-request", headers=student_h).status_code
        == 200
    )
    # atamayı 49 saat geriye çek
    from app import db as db_module
    from app.models.tables import MentorshipRequest

    with db_module.SessionLocal() as s:
        r = s.query(MentorshipRequest).one()
        r.assigned_at = datetime.now(timezone.utc) - timedelta(hours=49)
        s.commit()

    mine = client.get("/mentor-requests", headers=student_h).json()["requests"]
    assert mine[0]["status"] == "expired"
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 3


def test_authorization_boundaries(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "A")
    stranger_h, _ = _user(client, "B")
    sid = _submit(client, student_h)

    # başkasının ödevine istek → 404
    assert (
        client.post(f"/submissions/{sid}/mentor-request", headers=stranger_h).status_code
        == 404
    )
    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()

    # atanmamış kullanıcı feedback yazamaz (onaylı mentor değil / atanmadı)
    fb = f"/mentor-requests/{req['request_id']}/feedback"
    assert client.post(fb, json={"feedback_text": "x"}, headers=stranger_h).status_code == 403

    # admin olmayan onaylayamaz
    assert (
        client.post("/admin/mentor-applications/1/approve", headers=stranger_h).status_code
        == 403
    )

    # onaylı olmayan kullanıcı mentor kuyruğuna giremez
    assert client.get("/mentor/queue", headers=stranger_h).status_code == 403


def test_apply_rules_and_portfolio(client, monkeypatch):
    _enable_market(monkeypatch)
    h, _ = _user(client, "Aday")
    sid = _submit(client, h)

    # başkasının çizimi portfolyoya giremez
    other_h, _ = _user(client, "Diğer")
    other_sid = _submit(client, other_h)
    r = client.post(
        "/mentors/apply",
        json={"bio": "x", "portfolio_submission_ids": [other_sid]},
        headers=h,
    )
    assert r.status_code == 422

    # geçerli başvuru: portfolyo çizimi public olur
    r = client.post(
        "/mentors/apply",
        json={"bio": "x", "styles": ["realist"], "portfolio_submission_ids": [sid]},
        headers=h,
    )
    assert r.status_code == 200
    assert client.get(f"/submissions/{sid}/image", headers=other_h).status_code == 200

    # bekleyen başvuru varken ikinci başvuru 409
    assert client.post("/mentors/apply", json={"bio": "y"}, headers=h).status_code == 409


def test_account_deletion_with_mentor_data(client, monkeypatch):
    """Mentor hesabı silinince açık istekler iade edilir; öğrenci silinince kayıtları gider."""
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Silinecek Öğrencinin Mentoru Test")
    sid = _submit(client, student_h)
    assert (
        client.post(f"/submissions/{sid}/mentor-request", headers=student_h).status_code
        == 200
    )
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 2

    # mentor hesabını siler → öğrencinin jetonu iade
    assert client.delete("/users/me", headers=mentor_h).json()["deleted"] is True
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 3
    mine = client.get("/mentor-requests", headers=student_h).json()["requests"]
    assert mine[0]["status"] == "expired"

    # öğrenci de silinebilir (Faz 2 tabloları FK engeli çıkarmaz)
    assert client.delete("/users/me", headers=student_h).json()["deleted"] is True
