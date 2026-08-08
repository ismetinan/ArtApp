"""Jeton = AI ekonomisi (2026-08-08 kararı), JETON_AI_ECONOMY_ENABLED açıkken.

Bayrak KAPALI davranışı eski test dosyaları koruyor (test_mentors, test_direct_mentor,
test_earnings) — burada yalnız yeni model doğrulanıyor:

- jeton AI kullanım birimi; haftalık TABANA tamamlanır, birikmez, satın alınan
  jetona dokunulmaz,
- mentorluk ÜCRETSİZ; spam'i üç kota tutuyor (açık istek sayısı, mentor cooldown,
  mentor kutusu tavanı),
- mentora para yalnız uygulama dışı bağışla; link beyaz listeli ve admin onaylı.
"""

import io
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_billing import _enable_billing, _mock_play
from tests.test_mentors import PNG, _enable_market, _make_admin, _user

LONG_CRITIQUE = (
    "Omuz hattındaki açı biraz dik durmuş; klavikula çizgisini hafifçe aşağı "
    "eğerek göğüs kafesiyle ilişkisini netleştirebilirsin. Işık sol üstten "
    "geliyor ama boyun altındaki gölge aynı yönü takip etmiyor, o alanı bir "
    "kademe koyulaştırmak formu oturtur. Çizgi kalitesi genel olarak temiz, "
    "özellikle dış kontur akıcı; iç detaylarda ise çizgi ağırlığını biraz "
    "azaltmak derinlik hissini artırır. Devam et, temel oranlar sağlam."
)


@pytest.fixture
def economy(monkeypatch):
    """Yeni ekonomiyi açar ve ayarları test için erişilebilir kılar."""
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "jeton_ai_economy_enabled", True)
    monkeypatch.setattr(s, "mentor_market_enabled", True)
    return s


def _balance(client, headers) -> int:
    return client.get("/profile", headers=headers).json()["jeton_balance"]


def _rewind_weekly(user_id: int, days: int = 8) -> None:
    """Haftalık pencereyi açmak için sayacı geriye alır."""
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        u = s.get(User, user_id)
        u.free_jeton_last_grant = datetime.now(timezone.utc) - timedelta(days=days)
        s.commit()


def _set_paid(user_id: int, total: int, paid: int) -> None:
    """Satın alınmış jetonu simüle eder (billing akışını kurmadan)."""
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        u = s.get(User, user_id)
        u.jeton_balance = total
        u.jeton_paid_balance = paid
        s.commit()


def _submit_free(client, headers, node="cizgi-temelleri"):
    """Ödev gönderimi — yeni ekonomide 1 jeton harcar."""
    return client.post(
        f"/skill-tree/{node}/submit",
        files={"file": ("odev.png", io.BytesIO(PNG), "image/png")},
        headers=headers,
    )


def _apply_mentor(client, headers, **over):
    body = {
        "bio": "10 yıl karakter çizeri",
        "styles": ["manga"],
        "sample_critique": LONG_CRITIQUE,
        "rules_accepted": True,
    }
    body.update(over)
    return client.post("/mentors/apply", json=body, headers=headers)


def _approved_mentor(client, name="Mentor", **over):
    """Yeni ekonomiye uygun (kritik + kural onayı) başvuru + admin onayı."""
    mentor_h, mdata = _user(client, name)
    r = _apply_mentor(client, mentor_h, **over)
    assert r.status_code == 200, r.text
    admin_h, _ = _user(client, f"Admin{name}")
    _make_admin(client, admin_h)
    apps = client.get("/admin/mentor-applications", headers=admin_h).json()["applications"]
    target = next(a for a in apps if a["display_name"] == name)
    r = client.post(
        f"/admin/mentor-applications/{target['id']}/approve", headers=admin_h
    )
    assert r.json()["status"] == "approved"
    return mentor_h, mdata, admin_h, target["id"]


# ---------- Haftalık jeton tabanı ----------


def test_weekly_topup_fills_to_floor_and_does_not_accumulate(client, economy):
    """Taban altındaysa tabana tamamlar; taban doluysa jeton EKLEMEZ (birikmez)."""
    h, data = _user(client, "Taban")
    assert _balance(client, h) == 3  # hoşgeldin = taban

    # 1 jeton harcayıp pencereyi aç → 3'e tamamlanmalı (2 değil 3)
    assert _submit_free(client, h).status_code == 200
    assert _balance(client, h) == 2
    _rewind_weekly(data["id"])
    assert _balance(client, h) == 3

    # Taban zaten dolu: pencere yeniden açılsa da 3'te kalır, 6 olmaz
    _rewind_weekly(data["id"])
    assert _balance(client, h) == 3


def test_weekly_topup_never_touches_purchased_jetons(client, economy):
    """Satın alınan jeton silinmez, azalmaz ve tabanı doldurmuş sayılmaz.

    Kullanım Koşulları'ndaki "satın alınan jetonların süresi dolmaz" taahhüdü."""
    h, data = _user(client, "Alıcı")
    # Ücretsiz 0, satın alınmış 10 → toplam 10
    _set_paid(data["id"], total=10, paid=10)
    _rewind_weekly(data["id"])

    p = client.get("/profile", headers=h).json()
    # Ücretsiz bileşen 0'dan 3'e çıkar; altın 10 aynen durur → toplam 13
    assert p["jeton_balance"] == 13
    assert p["gold_jeton_balance"] == 10


def test_premium_gets_higher_floor(client, economy, monkeypatch):
    h, data = _user(client, "Premium")
    monkeypatch.setattr(economy, "weekly_jeton_floor_premium", 25)
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        u.premium_until = datetime.now(timezone.utc) + timedelta(days=30)
        s.commit()
    _rewind_weekly(data["id"])
    assert _balance(client, h) == 25


# ---------- AI harcaması ----------


def test_redline_costs_one_jeton_then_402(client, economy):
    h, _ = _user(client, "Çizer")
    for expected in (2, 1, 0):
        assert _submit_free(client, h).status_code == 200
        assert _balance(client, h) == expected

    r = _submit_free(client, h)
    assert r.status_code == 402
    assert _balance(client, h) == 0  # başarısız istek bakiyeyi bozmaz


def test_402_message_mentions_store_only_when_billing_enabled(client, economy, monkeypatch):
    """Mağazası olmayan platformda "mağazadan al" demek çıkmaz sokak."""
    h, _ = _user(client, "Mesaj")
    for _ in range(3):
        assert _submit_free(client, h).status_code == 200

    detail = _submit_free(client, h).json()["detail"]
    assert "her hafta" in detail.lower()  # jeton_insufficient_no_store

    monkeypatch.setattr(economy, "billing_enabled", True)
    detail = _submit_free(client, h).json()["detail"]
    assert "mağaza" in detail.lower()  # jeton_insufficient


def test_failed_ai_call_refunds_the_jeton(client, economy, monkeypatch):
    """AI patlarsa jeton geri sarılır — en kritik garanti: ödeme yapılan bir
    kaynağı başarısız bir çağrı için almıyoruz."""
    h, _ = _user(client, "Hata")
    assert _balance(client, h) == 3

    async def boom(*a, **kw):
        raise RuntimeError("model meşgul")

    from app.ai.mock import MockAIProvider

    monkeypatch.setattr(MockAIProvider, "redline_analysis", boom)
    r = _submit_free(client, h)
    assert r.status_code == 503
    assert _balance(client, h) == 3  # harcama commit edilmedi


def test_onboarding_and_assignment_are_free(client, economy):
    h, _ = _user(client, "Bedava")
    files = [
        ("files", ("a.png", io.BytesIO(PNG), "image/png")),
        ("files", ("b.png", io.BytesIO(PNG), "image/png")),
        ("files", ("c.png", io.BytesIO(PNG), "image/png")),
    ]
    assert client.post("/onboarding/assess", files=files, headers=h).status_code == 200
    assert _balance(client, h) == 3  # seviye belirleme ücretsiz

    r = client.post("/skill-tree/cizgi-temelleri/assignment", headers=h)
    assert r.status_code == 200
    assert _balance(client, h) == 3  # ödev üretimi de ücretsiz


def test_free_analysis_has_no_weekly_window_in_new_economy(client, economy):
    """Yeni ekonomide haftalık pencere kalkar — kıtlığı jeton tabanı yaratıyor.
    İki kısıtı üst üste bindirmek kullanıcıya iki kez ceza olurdu."""
    h, _ = _user(client, "Serbest")
    for expected in (2, 1):
        r = client.post(
            "/free-analysis",
            files={"file": ("s.png", io.BytesIO(PNG), "image/png")},
            headers=h,
        )
        assert r.status_code == 200, r.text
        assert _balance(client, h) == expected


# ---------- Mentorluk ücretsiz + kotalar ----------


def test_mentor_request_is_free(client, economy):
    mentor_h, _, _, _ = _approved_mentor(client)
    student_h, sdata = _user(client, "Öğrenci")
    # Bakiyeyi tamamen tüket: mentorluk yine çalışmalı
    _set_paid(sdata["id"], total=0, paid=0)
    sid = _submit_via_mentor_fixture(client, student_h, sdata)

    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 200, r.text
    assert r.json()["jeton_balance"] == 0  # hiç jeton harcanmadı


def _submit_via_mentor_fixture(client, headers, data):
    """Ödev gönderimi jetonsuz yapılamaz; bakiyeyi geçici verip sonra sıfırlar."""
    _set_paid(data["id"], total=1, paid=0)
    r = _submit_free(client, headers)
    assert r.status_code == 200, r.text
    _set_paid(data["id"], total=0, paid=0)
    return r.json()["submission_id"]


def test_max_open_requests_and_stale_does_not_lock_out(client, economy):
    """4. açık istek 409; süresi geçmiş istekler slotu serbest bırakır.

    İkinci kısım kritik: zaman aşımı tembel işliyor, kota kontrolünden önce
    çalıştırılmazsa 48 saati geçmiş 3 istek öğrenciyi kalıcı kilitler."""
    from app import db as db_module
    from app.models.tables import MentorshipRequest

    for i in range(4):
        _approved_mentor(client, name=f"M{i}")
    student_h, sdata = _user(client, "Çok")

    sids = []
    for _ in range(4):
        sids.append(_submit_via_mentor_fixture(client, student_h, sdata))

    for sid in sids[:3]:
        r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
        assert r.status_code == 200, r.text

    r = client.post(f"/submissions/{sids[3]}/mentor-request", headers=student_h)
    assert r.status_code == 409
    assert "3" in r.json()["detail"]

    # Açık istekleri 48 saatten eskiye çek → slot açılmalı (kilitlenme yok)
    with db_module.SessionLocal() as s:
        old = datetime.now(timezone.utc) - timedelta(hours=72)
        for req in s.query(MentorshipRequest).all():
            req.assigned_at = old
            req.created_at = old
        s.commit()

    r = client.post(f"/submissions/{sids[3]}/mentor-request", headers=student_h)
    assert r.status_code == 200, r.text


def test_same_mentor_24h_cooldown_selective(client, economy):
    mentor_h, mdata, _, profile_id = _approved_mentor(client)
    student_h, sdata = _user(client, "Israrcı")
    sid1 = _submit_via_mentor_fixture(client, student_h, sdata)
    sid2 = _submit_via_mentor_fixture(client, student_h, sdata)

    r = client.post(
        f"/submissions/{sid1}/mentor-request",
        json={"mentor_id": profile_id},
        headers=student_h,
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/submissions/{sid2}/mentor-request",
        json={"mentor_id": profile_id},
        headers=student_h,
    )
    assert r.status_code == 409
    assert "24" in r.json()["detail"]


def test_cooldown_excludes_mentor_from_pool(client, economy):
    """Havuzda mentor sonradan atanıyor → kota aday listesinden ÇIKARMA olarak
    uygulanır. Tek mentor varsa havuz boşalır ve no_mentor_available döner."""
    _approved_mentor(client, name="Tek")
    student_h, sdata = _user(client, "Havuz")
    sid1 = _submit_via_mentor_fixture(client, student_h, sdata)
    sid2 = _submit_via_mentor_fixture(client, student_h, sdata)

    assert client.post(
        f"/submissions/{sid1}/mentor-request", headers=student_h
    ).status_code == 200
    r = client.post(f"/submissions/{sid2}/mentor-request", headers=student_h)
    assert r.status_code == 409
    assert "mentor" in r.json()["detail"].lower()


def test_mentor_inbox_cap(client, economy, monkeypatch):
    """Mentor kutusu dolunca seçmeli istek 409, havuz adaylığı düşer."""
    import app.api.mentors as m

    monkeypatch.setattr(m, "MENTOR_INBOX_CAP", 2)
    monkeypatch.setattr(m, "MENTOR_COOLDOWN", timedelta(seconds=0))  # cooldown'ı ayır
    _, _, _, profile_id = _approved_mentor(client, name="Dolu")

    # İki ayrı öğrenci mentorun kutusunu doldurur
    for name in ("A", "B"):
        h, d = _user(client, name)
        sid = _submit_via_mentor_fixture(client, h, d)
        r = client.post(
            f"/submissions/{sid}/mentor-request",
            json={"mentor_id": profile_id},
            headers=h,
        )
        assert r.status_code == 200, r.text

    h, d = _user(client, "C")
    sid = _submit_via_mentor_fixture(client, h, d)
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": profile_id}, headers=h
    )
    assert r.status_code == 409
    # Havuzda da tek aday o mentor olduğu için havuz boşalır
    assert client.post(
        f"/submissions/{sid}/mentor-request", headers=h
    ).status_code == 409


def test_expired_free_request_sends_no_refund_message(client, economy):
    """Ücretsiz mentorlukta iade yok → "jetonun iade edildi" bildirimi de yok."""
    from app import db as db_module
    from app.models.tables import JetonTransaction, MentorshipRequest

    _approved_mentor(client, name="Yavaş")
    student_h, sdata = _user(client, "Bekleyen")
    sid = _submit_via_mentor_fixture(client, student_h, sdata)
    client.post(f"/submissions/{sid}/mentor-request", headers=student_h)

    with db_module.SessionLocal() as s:
        req = s.query(MentorshipRequest).one()
        req.assigned_at = datetime.now(timezone.utc) - timedelta(hours=72)
        s.commit()

    client.get("/mentor-requests", headers=student_h)
    with db_module.SessionLocal() as s:
        assert s.query(MentorshipRequest).one().status == "expired"
        # İade satırı yazılmamalı (jeton_cost=0)
        assert s.query(JetonTransaction).filter_by(reason="refund").count() == 0


# ---------- Mentor başvurusu: kalite kapısı ----------


def test_sample_critique_and_rules_required(client, economy):
    h, _ = _user(client, "Aday")
    r = _apply_mentor(client, h, sample_critique="kısa")
    assert r.status_code == 422
    assert "200" in r.json()["detail"]

    r = _apply_mentor(client, h, rules_accepted=False)
    assert r.status_code == 422

    assert _apply_mentor(client, h).status_code == 200


def test_reapply_cooldown_after_rejection(client, economy):
    from app import db as db_module
    from app.models.tables import MentorProfile

    h, _ = _user(client, "Reddedilen")
    assert _apply_mentor(client, h).status_code == 200
    admin_h, _ = _user(client, "Admin")
    _make_admin(client, admin_h)
    apps = client.get("/admin/mentor-applications", headers=admin_h).json()["applications"]
    client.post(f"/admin/mentor-applications/{apps[0]['id']}/reject", headers=admin_h)

    r = _apply_mentor(client, h)
    assert r.status_code == 409
    assert "14" in r.json()["detail"]

    # 14 günden eski ret → yeniden başvurabilir
    with db_module.SessionLocal() as s:
        p = s.query(MentorProfile).one()
        p.rejected_at = datetime.now(timezone.utc) - timedelta(days=15)
        s.commit()
    assert _apply_mentor(client, h).status_code == 200


# ---------- Bağış ----------


def test_donation_url_whitelist(client, economy):
    h, _ = _user(client, "Bağışçı")
    for bad in (
        "https://evil.example.com/pay",
        "http://kreosus.com/artora",  # https zorunlu
        "https://kreosus.com.evil.net/x",  # son ek oyunu
    ):
        r = _apply_mentor(client, h, donation_url=bad)
        assert r.status_code == 422, bad
        assert "Kreosus" in r.json()["detail"]

    r = _apply_mentor(client, h, donation_url="https://kreosus.com/artora")
    assert r.status_code == 200
    me = client.get("/mentor/me", headers=h).json()
    assert me["donation_platform"] == "Kreosus"
    assert me["donation_status"] == "pending"  # onaya kadar gösterilmez


def test_iban_in_text_rejected(client, economy):
    h, _ = _user(client, "IBAN")
    r = _apply_mentor(client, h, bio="Destek: TR33 0006 1005 1978 6457 8413 26")
    assert r.status_code == 422
    assert "IBAN" in r.json()["detail"]


def test_donation_link_hidden_until_approved(client, economy):
    """Onaysız link öğrenciye gösterilmez; onaydan sonra profil detayında görünür
    ama mentor LİSTESİNDE hiç görünmez (Apple §3.2.1 çerçevesi)."""
    mentor_h, _, admin_h, profile_id = _approved_mentor(
        client, name="Destekli", donation_url="https://ko-fi.com/destekli"
    )
    student_h, _ = _user(client, "İzleyen")

    detail = client.get(f"/mentors/{profile_id}", headers=student_h).json()
    assert "donation_url" not in detail  # henüz onaysız

    r = client.post(
        f"/admin/mentor-profiles/{profile_id}/donation/approve", headers=admin_h
    )
    assert r.json()["donation_status"] == "approved"

    detail = client.get(f"/mentors/{profile_id}", headers=student_h).json()
    assert detail["donation_url"] == "https://ko-fi.com/destekli"
    assert detail["donation_platform"] == "Ko-fi"

    listed = client.get("/mentors", headers=student_h).json()["mentors"]
    assert all("donation_url" not in m for m in listed)


def test_flag_off_keeps_old_mentor_costs(client, monkeypatch):
    """Bayrak kapalıyken mentorluk yine 1 jeton — eski davranış korunuyor."""
    _enable_market(monkeypatch)
    from tests.test_mentors import _approved_mentor as old_mentor
    from tests.test_mentors import _submit as old_submit

    old_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Eski")
    sid = old_submit(client, student_h)
    r = client.post(f"/submissions/{sid}/mentor-request", headers=student_h)
    assert r.status_code == 200
    assert r.json()["jeton_balance"] == 2  # 3 - 1
