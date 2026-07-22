"""Faz 4 (gelir paylaşımı) Faz A: mentor kazanç defteri.

Kazanç yalnız istek cevaplanınca (answered) işlenir; jeton-eşdeğeri = öğrencinin
harcadığı jeton_cost (havuz=1, seçmeli=3). Aynı istek iki kez kredi vermez; expired
istek kredi vermez; uç yalnız onaylı mentora yanıt verir (para/güven akışı §6).
"""

from datetime import datetime, timedelta, timezone

from tests.test_mentors import _approved_mentor, _enable_market, _submit, _user


def _answer(client, mentor_h, request_id, text="Eline sağlık, omuz açısına dikkat."):
    r = client.post(
        f"/mentor-requests/{request_id}/feedback",
        json={"feedback_text": text},
        headers=mentor_h,
    )
    assert r.status_code == 200, r.text


def test_answering_credits_mentor_pool_one(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Öğrenci")
    sid = _submit(client, student_h)

    # cevaplamadan önce kazanç sıfır
    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 0,
        "answered_count": 0,
    }

    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()
    _answer(client, mentor_h, req["request_id"])

    # havuz isteği = 1 jeton-eşdeğeri
    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 1,
        "answered_count": 1,
    }


def test_direct_request_credits_three(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Seçici")
    sid = _submit(client, student_h)
    pid = client.get("/mentors", headers=student_h).json()["mentors"][0]["id"]

    req = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    ).json()
    _answer(client, mentor_h, req["request_id"])

    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 3,
        "answered_count": 1,
    }


def test_multiple_answers_accumulate(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Çok İsteyen")
    for node in ("cizgi-temelleri", "sekil-ve-form"):
        sid = _submit(client, student_h, node=node)
        req = client.post(
            f"/submissions/{sid}/mentor-request", headers=student_h
        ).json()
        _answer(client, mentor_h, req["request_id"])

    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 2,
        "answered_count": 2,
    }


def test_expired_request_earns_nothing(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Bekleyen")
    sid = _submit(client, student_h)
    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()

    # isteği 49 saat öncesine al → tembel zaman aşımı expired + iade
    from app import db as db_module
    from app.models.tables import MentorshipRequest

    with db_module.SessionLocal() as s:
        r = s.query(MentorshipRequest).one()
        r.assigned_at = datetime.now(timezone.utc) - timedelta(hours=49)
        s.commit()

    # mentor kuyruğu tetikler → expired; cevap denemesi 409
    client.get("/mentor/queue", headers=mentor_h)
    r = client.post(
        f"/mentor-requests/{req['request_id']}/feedback",
        json={"feedback_text": "geç kaldım"},
        headers=mentor_h,
    )
    assert r.status_code == 409
    assert client.get("/mentor/earnings", headers=mentor_h).json()["jeton_equivalent"] == 0


def test_earnings_requires_approved_mentor(client, monkeypatch):
    _enable_market(monkeypatch)
    # onaysız sıradan kullanıcı kazanç ucuna erişemez
    h, _ = _user(client, "Sıradan")
    assert client.get("/mentor/earnings", headers=h).status_code == 403


def test_earnings_flag_off_404(client):
    h, _ = _user(client, "X")
    assert client.get("/mentor/earnings", headers=h).status_code == 404


def test_backfill_credits_existing_answered(client, monkeypatch):
    """Migration backfill'i simüle eder: doğrudan DB'ye answered istek + kazançsız
    durum kur, earnings.credit'in idempotent + toplama davranışını doğrula."""
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Öğrenci")
    sid = _submit(client, student_h)
    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()
    _answer(client, mentor_h, req["request_id"])

    # aynı isteği yeniden kredilemek defteri şişirmemeli (request_id unique/idempotent)
    from app import db as db_module
    from app.models.tables import MentorshipRequest
    from app.services import earnings

    with db_module.SessionLocal() as s:
        r = s.query(MentorshipRequest).one()
        mentor_id = r.mentor_id
        earnings.credit(s, mentor_id, r)  # ikinci kez
        s.commit()
        assert earnings.summary(s, mentor_id) == {
            "jeton_equivalent": 1,
            "answered_count": 1,
        }
