"""Faz 4 (gelir paylaşımı) Faz A: mentor kazanç defteri.

Kazanç yalnız istek cevaplanınca (answered) işlenir; jeton-eşdeğeri = öğrencinin
harcadığı jeton_cost (havuz=1, seçmeli=3). Aynı istek iki kez kredi vermez; expired
istek kredi vermez; uç yalnız onaylı mentora yanıt verir (para/güven akışı §6).
"""

from datetime import datetime, timedelta, timezone

from tests.test_billing import _enable_billing, _mock_play
from tests.test_mentors import _approved_mentor, _enable_market, _submit, _user


def _paid_balance(user_id: int) -> int:
    """jeton_paid_balance'ı DB'den okur (API'de açık değil — iç muhasebe alanı)."""
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        return s.get(User, user_id).jeton_paid_balance


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
        "paid_equivalent": 0,
        "answered_count": 0,
    }

    req = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()
    _answer(client, mentor_h, req["request_id"])

    # havuz isteği = 1 jeton-eşdeğeri; ücretsiz hoşgeldin jetonuyla ödendi → paid=0
    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 1,
        "paid_equivalent": 0,
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

    # 3 ücretsiz hoşgeldin jetonuyla ödendi → jeton_equivalent 3, paid 0
    assert client.get("/mentor/earnings", headers=mentor_h).json() == {
        "jeton_equivalent": 3,
        "paid_equivalent": 0,
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
        "paid_equivalent": 0,
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


def test_welcome_jetons_are_free(client):
    _, data = _user(client, "Yeni")
    assert client.get("/profile", headers={"Authorization": f"Bearer {data['token']}"}
                      ).json()["jeton_balance"] == 3
    assert _paid_balance(data["id"]) == 0  # hoşgeldin jetonları gelir-destekli DEĞİL


def _buy_jeton_5(client, headers, token="tok-earn"):
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_5", "purchase_token": token},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["jeton_balance"]


def test_paid_jetons_tracked_and_earned(client, monkeypatch):
    """Satın alınmış jeton gelir-destekli sayılır; önce-ücretsiz kuralıyla harcanınca
    mentorun nakde çevrilebilir kazancına (paid_equivalent) taşınır."""
    _enable_market(monkeypatch)
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, sdata = _user(client, "Alıcı Öğrenci")

    # 3 ücretsiz + 5 satın alınmış = 8 (paid_balance=5)
    assert _buy_jeton_5(client, student_h) == 8
    assert _paid_balance(sdata["id"]) == 5

    # İlk seçmeli istek (3): önce-ücretsiz → 3 ücretsiz jeton harcanır, paid_spent=0
    sid1 = _submit(client, student_h, node="cizgi-temelleri")
    pid = client.get("/mentors", headers=student_h).json()["mentors"][0]["id"]
    req1 = client.post(
        f"/submissions/{sid1}/mentor-request", json={"mentor_id": pid}, headers=student_h
    ).json()
    assert req1["jeton_balance"] == 5
    assert _paid_balance(sdata["id"]) == 5  # ücretsizler gitti, gelir-destekli durur
    _answer(client, mentor_h, req1["request_id"])
    e = client.get("/mentor/earnings", headers=mentor_h).json()
    assert e == {"jeton_equivalent": 3, "paid_equivalent": 0, "answered_count": 1}

    # İkinci seçmeli istek (3): ücretsiz kalmadı → 3'ü de gelir-destekli, paid_spent=3
    sid2 = _submit(client, student_h, node="sekil-ve-form")
    req2 = client.post(
        f"/submissions/{sid2}/mentor-request", json={"mentor_id": pid}, headers=student_h
    ).json()
    assert req2["jeton_balance"] == 2
    assert _paid_balance(sdata["id"]) == 2
    _answer(client, mentor_h, req2["request_id"])
    e = client.get("/mentor/earnings", headers=mentor_h).json()
    # toplam 6 kazanç, bunun 3'ü nakde çevrilebilir
    assert e == {"jeton_equivalent": 6, "paid_equivalent": 3, "answered_count": 2}


def test_refund_restores_paid_composition(client, monkeypatch):
    """Zaman aşımı iadesi, harcanan gelir-destekli/ücretsiz bileşimi aynen geri
    yükler — kaynak muhasebesi bozulmaz."""
    _enable_market(monkeypatch)
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, sdata = _user(client, "İade Öğrenci")

    _buy_jeton_5(client, student_h)  # 3 ücretsiz + 5 paid = 8
    # ücretsizleri tüketmek için 3 havuz isteği (her biri cevaplanır, iade yok)
    for node in ("cizgi-temelleri", "sekil-ve-form", "jest-cizimi"):
        sid = _submit(client, student_h, node=node)
        rq = client.post(f"/submissions/{sid}/mentor-request", headers=student_h).json()
        _answer(client, mentor_h, rq["request_id"])
    assert _paid_balance(sdata["id"]) == 5  # 3 ücretsiz gitti, 5 paid durur

    # şimdi seçmeli (3) → 3 paid harcanır → paid_balance 2
    sid = _submit(client, student_h, node="temel-oranlar")
    pid = client.get("/mentors", headers=student_h).json()["mentors"][0]["id"]
    rq = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=student_h
    ).json()
    assert _paid_balance(sdata["id"]) == 2

    # isteği zaman aşımına uğrat → iade paid bileşimini geri yükler
    from app import db as db_module
    from app.models.tables import MentorshipRequest

    with db_module.SessionLocal() as s:
        r = s.get(MentorshipRequest, rq["request_id"])
        r.assigned_at = datetime.now(timezone.utc) - timedelta(hours=49)
        s.commit()
    client.get("/mentor-requests", headers=student_h)  # tembel iade tetikler
    assert client.get("/profile", headers=student_h).json()["jeton_balance"] == 5
    assert _paid_balance(sdata["id"]) == 5  # 3 paid geri geldi


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
            "paid_equivalent": 0,
            "answered_count": 1,
        }
