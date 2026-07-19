"""Play Billing: doğrulama, idempotency, premium kota (Play API mock'lu)."""

from datetime import datetime, timedelta, timezone

from tests.test_mentors import _user


def _enable_billing(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "billing_enabled", True)


def _mock_play(monkeypatch, *, expiry=None, fail=False):
    """Play API fonksiyonlarını mock'lar; acknowledge çağrılarını sayar."""
    import app.services.billing as billing

    acks = []

    def fake_product(product_id, token):
        if fail:
            raise billing.PlayVerifyError("mock: geçersiz token")
        return {"purchaseState": 0}

    def fake_subscription(token):
        if fail:
            raise billing.PlayVerifyError("mock: geçersiz token")
        return {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "lineItems": [{"expiryTime": (expiry or _next_month()).isoformat()}],
        }

    monkeypatch.setattr(billing, "verify_product_with_play", fake_product)
    monkeypatch.setattr(billing, "verify_subscription_with_play", fake_subscription)
    monkeypatch.setattr(
        billing, "acknowledge_with_play", lambda kind, pid, tok: acks.append(pid)
    )
    return acks


def _next_month():
    return datetime.now(timezone.utc) + timedelta(days=30)


def test_billing_disabled_404(client):
    h, _ = _user(client, "Bayraksız")
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_5", "purchase_token": "t"},
        headers=h,
    )
    assert r.status_code == 404


def test_jeton_pack_grants_and_is_idempotent(client, monkeypatch):
    _enable_billing(monkeypatch)
    acks = _mock_play(monkeypatch)
    h, _ = _user(client, "Alıcı")

    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_5", "purchase_token": "tok-a"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["jeton_balance"] == 8  # 3 hoşgeldin + 5
    assert acks == ["jeton_5"]

    # Aynı token tekrar → hak verilmez, yine 200
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_5", "purchase_token": "tok-a"},
        headers=h,
    )
    assert r.status_code == 200 and r.json()["jeton_balance"] == 8

    # Ledger'da tek "purchase" satırı olmalı
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import JetonTransaction

    with db_module.SessionLocal() as s:
        rows = s.execute(
            select(JetonTransaction).where(JetonTransaction.reason == "purchase")
        ).scalars().all()
        assert len(rows) == 1 and rows[0].delta == 5


def test_invalid_token_400_no_grant(client, monkeypatch):
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch, fail=True)
    h, _ = _user(client, "Şüpheli")
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_15", "purchase_token": "sahte"},
        headers=h,
    )
    assert r.status_code == 400
    assert client.get("/profile", headers=h).json()["jeton_balance"] == 3

    # Tanınmayan ürün de 400
    r = client.post(
        "/billing/verify",
        json={"product_id": "jeton_999", "purchase_token": "x"},
        headers=h,
    )
    assert r.status_code == 400


def test_subscription_sets_premium_and_monthly_grant_once(client, monkeypatch):
    _enable_billing(monkeypatch)
    expiry = _next_month()
    _mock_play(monkeypatch, expiry=expiry)
    h, _ = _user(client, "Premium Aday")

    r = client.post(
        "/billing/verify",
        json={"product_id": "premium_monthly", "purchase_token": "sub-1"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_premium"] is True
    assert body["jeton_balance"] == 13  # 3 + aylık 10

    # Aynı dönem yeniden doğrulanırsa jeton TEKRAR verilmez
    r = client.get("/billing/status", headers=h)
    assert r.json()["jeton_balance"] == 13

    # Yeni fatura dönemi (expiry ileri gitti) → aylık jeton bir kez daha
    _mock_play(monkeypatch, expiry=expiry + timedelta(days=30))
    r = client.get("/billing/status", headers=h)
    assert r.json()["jeton_balance"] == 23
    assert r.json()["is_premium"] is True


def test_premium_raises_ai_quota(client, monkeypatch):
    _enable_billing(monkeypatch)
    _mock_play(monkeypatch)
    h, data = _user(client, "Kotalı")

    # Ücretsiz limiti 0'a çek: normal kullanıcı anında 429 alır
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ai_daily_limit", 0)

    from app import db as db_module
    from app.models.tables import User
    from app.services.quota import consume_ai_quota

    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        try:
            consume_ai_quota(s, u)
            raised = False
        except Exception:
            raised = True
        assert raised

    # Premium yap → premium limit (50) geçerli, çağrı geçer
    client.post(
        "/billing/verify",
        json={"product_id": "premium_monthly", "purchase_token": "sub-q"},
        headers=h,
    )
    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        consume_ai_quota(s, u)  # fırlatmamalı
        s.commit()


def test_profile_exposes_billing_fields(client, monkeypatch):
    _enable_billing(monkeypatch)
    h, _ = _user(client, "Profilci")
    p = client.get("/profile", headers=h).json()
    assert p["billing_enabled"] is True
    assert p["is_premium"] is False and p["premium_until"] is None
