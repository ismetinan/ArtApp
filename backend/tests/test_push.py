"""FCM push: cihaz kaydı, olay bağlantıları ve hata izolasyonu.

Gerçek Firebase çağrısı yok — send_push monkeypatch'lenir; testler doğru
alıcı+doğru dilde metinle çağrıldığını ve push hatasının akışı bozmadığını
doğrular. Ortak akış yardımcıları test_mentors ile aynı desendedir.
"""

import io

from tests.test_mentors import _approved_mentor, _enable_market, _submit, _user

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _capture_pushes(monkeypatch):
    import app.api.mentors as mentors_module

    sent = []
    monkeypatch.setattr(
        mentors_module, "send_push", lambda user, title, body: sent.append((user.id, title, body))
    )
    return sent


def test_register_device(client):
    _, data = _user(client, "Cihazlı")
    h = {"Authorization": f"Bearer {data['token']}"}
    r = client.put("/users/me/device", json={"fcm_token": "tok-123"}, headers=h)
    assert r.status_code == 200 and r.json()["ok"] is True

    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        u = s.execute(select(User).where(User.id == data["id"])).scalar_one()
        assert u.fcm_token == "tok-123"


def test_push_events_new_request_and_feedback(client, monkeypatch):
    _enable_market(monkeypatch)
    sent = _capture_pushes(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)  # display_name "Mentor", dil tr
    student_h, student = _user(client, "Öğrenci")
    sid = _submit(client, student_h)

    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()
    # 1) mentora "yeni istek" bildirimi, öğrenci adıyla
    assert len(sent) == 1
    _, title, body = sent[0]
    assert "Yeni mentor isteği" in title and "Öğrenci" in body

    client.post(
        f"/mentor-requests/{req['request_id']}/feedback",
        json={"feedback_text": "Eline sağlık"},
        headers=mentor_h,
    )
    # 2) öğrenciye "cevap geldi" bildirimi, mentor adıyla, öğrencinin id'sine
    assert len(sent) == 2
    uid, title, body = sent[1]
    assert uid == student["id"] and "mentor cevabı" in title and "Mentor" in body


def test_push_event_on_refund(client, monkeypatch):
    from datetime import datetime, timedelta, timezone

    _enable_market(monkeypatch)
    sent = _capture_pushes(monkeypatch)
    _approved_mentor(client, monkeypatch)
    student_h, student = _user(client, "Bekleyen")
    sid = _submit(client, student_h)
    client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    sent.clear()

    from app import db as db_module
    from app.models.tables import MentorshipRequest

    with db_module.SessionLocal() as s:
        r = s.query(MentorshipRequest).one()
        r.assigned_at = datetime.now(timezone.utc) - timedelta(hours=49)
        s.commit()

    client.get("/mentor-requests", headers=student_h)
    assert len(sent) == 1
    uid, title, _ = sent[0]
    assert uid == student["id"] and "iade" in title.lower()


def test_broken_firebase_config_does_not_break_flow(client, monkeypatch):
    """Firebase yapılandırması bozuk olsa bile send_push fırlatmaz, akış 200 döner."""
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    # Alıcının token'ı olmalı ki send_push init'e kadar ilerlesin
    client.put("/users/me/device", json={"fcm_token": "tok-m"}, headers=mentor_h)
    student_h, _ = _user(client, "Sağlam")
    sid = _submit(client, student_h)

    from app.core.config import get_settings
    from app.services import push as push_service

    monkeypatch.setattr(get_settings(), "firebase_service_account_json", "bozuk-json{")
    monkeypatch.setattr(push_service, "_app", None)
    monkeypatch.setattr(push_service, "_init_failed", False)

    # gerçek send_push devrede (mentors.py'dan import edilen referans) — init
    # patlar, loglanır, istek yine de başarılı olur
    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 200
    assert push_service._init_failed is True


def test_send_push_noop_without_config():
    """FIREBASE_SERVICE_ACCOUNT_JSON boşken send_push sessizce döner."""
    from app.models.tables import User
    from app.services.push import send_push

    u = User(id=1, display_name="X", api_token="t", fcm_token="tok")
    send_push(u, "başlık", "gövde")  # istisna fırlatmamalı

    u2 = User(id=2, display_name="Y", api_token="t2", fcm_token=None)
    send_push(u2, "başlık", "gövde")  # token yok → anında no-op
