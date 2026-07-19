"""Müşteri geri bildirimi paketi: skor-atlama, öneri, AI ödev, serbest analiz, waitlist."""

import io

from tests.test_mentors import _user

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _set_score(user_id, axis, score):
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import AbilityScore

    with db_module.SessionLocal() as s:
        row = s.execute(
            select(AbilityScore).where(
                AbilityScore.user_id == user_id, AbilityScore.axis == axis
            )
        ).scalar_one_or_none()
        if row is None:
            s.add(AbilityScore(user_id=user_id, axis=axis, score=score))
        else:
            row.score = score
        s.commit()


def _tree(client, headers):
    r = client.get("/skill-tree", headers=headers)
    assert r.status_code == 200
    return r.json()


def _node(tree, node_id):
    return next(n for n in tree["nodes"] if n["id"] == node_id)


def test_score_skip_unlocks_node(client):
    h, data = _user(client, "Atlayan")
    # cizgi-temelleri (eksen: cizgi_kalitesi) tamamlanmadı; skor eşik altı → kilitli
    _set_score(data["id"], "cizgi_kalitesi", 59)
    t = _tree(client, h)
    assert _node(t, "sekil-ve-form")["status"] == "locked"

    # Eşik (60) ve üstü → önkoşul atlanır, düğüm skorla açılır
    _set_score(data["id"], "cizgi_kalitesi", 60)
    t = _tree(client, h)
    n = _node(t, "sekil-ve-form")
    assert n["status"] == "available" and n["unlocked_by_score"] is True
    # Kök düğüm normal available — skor rozeti yok
    assert _node(t, "cizgi-temelleri")["unlocked_by_score"] is False

    # Skorla açılan düğüme ödev de gönderilebilmeli (403 yok)
    r = client.post(
        "/skill-tree/sekil-ve-form/submit",
        files={"file": ("odev.png", io.BytesIO(PNG), "image/png")},
        headers=h,
    )
    assert r.status_code == 200, r.text


def test_recommended_node_targets_weakest_axis(client):
    h, data = _user(client, "Yönlenen")
    t = _tree(client, h)
    # Skor yokken de bir öneri döner (available düğümlerden biri)
    assert t["recommended_node_id"] is not None

    # perspektif en zayıf eksen + şekil-ve-form skorla açık → öneri oraya döner
    # (skorsuz eksen 0 sayılır; bu yüzden diğer açık düğümlerin eksenleri doldurulur)
    _set_score(data["id"], "cizgi_kalitesi", 80)
    _set_score(data["id"], "perspektif", 5)
    _set_score(data["id"], "oran", 50)
    _set_score(data["id"], "anatomi", 50)
    t = _tree(client, h)
    rec = _node(t, t["recommended_node_id"])
    assert rec["skill_axis"] == "perspektif"


def test_assignment_generate_cache_and_quota(client):
    h, _ = _user(client, "Ödevci")
    # Kayıt yokken GET null döner, kota harcamaz
    r = client.get("/skill-tree/cizgi-temelleri/assignment", headers=h)
    assert r.status_code == 200 and r.json()["assignment"] is None

    # POST üretir (mock: obje + farklı açılar görevi)
    r = client.post("/skill-tree/cizgi-temelleri/assignment", headers=h)
    assert r.status_code == 200
    text = r.json()["assignment"]
    assert "açı" in text or "angle" in text

    # İkinci POST önbellekten döner — kota düşmez
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import AiUsage

    with db_module.SessionLocal() as s:
        count_before = s.execute(select(AiUsage)).scalars().one().count
    r = client.post("/skill-tree/cizgi-temelleri/assignment", headers=h)
    assert r.json()["assignment"] == text
    with db_module.SessionLocal() as s:
        assert s.execute(select(AiUsage)).scalars().one().count == count_before

    # Var olmayan düğüm → 404
    assert client.post("/skill-tree/yok/assignment", headers=h).status_code == 404


def test_free_analysis_weekly_limit_and_premium(client):
    from datetime import datetime, timedelta, timezone

    h, data = _user(client, "Serbest")
    files = {"file": ("resim.png", io.BytesIO(PNG), "image/png")}
    r = client.post("/free-analysis", files=files, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["xp_awarded"] == 0

    # Aynı hafta ikinci deneme → 429
    files = {"file": ("resim2.png", io.BytesIO(PNG), "image/png")}
    r = client.post("/free-analysis", files=files, headers=h)
    assert r.status_code == 429

    # Premium kullanıcıda haftalık sınır yok
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as s:
        u = s.get(User, data["id"])
        u.premium_until = datetime.now(timezone.utc) + timedelta(days=30)
        s.commit()
    files = {"file": ("resim3.png", io.BytesIO(PNG), "image/png")}
    assert client.post("/free-analysis", files=files, headers=h).status_code == 200

    # Serbest çalışmalar Gelişim Macerası'nda listelenir
    gallery = client.get("/profile", headers=h).json()["gelisim_macerasi"]
    assert sum(1 for g in gallery if g["node_id"] is None) == 2


def test_waitlist_signup_dedupe_and_admin_list(client):
    r = client.post("/waitlist", json={"email": "Test@Example.com", "language": "tr"})
    assert r.status_code == 200
    # Aynı e-posta (farklı büyük/küçük harf) → yine 200, tek kayıt
    r = client.post("/waitlist", json={"email": "test@example.com", "language": "en"})
    assert r.status_code == 200

    from tests.test_mentors import _make_admin

    h, data = _user(client, "Yönetici")
    _make_admin(client, h)
    listing = client.get("/admin/waitlist", headers=h).json()
    assert listing["count"] == 1
    assert listing["signups"][0]["email"] == "test@example.com"

    # Admin olmayan 403
    h2, _ = _user(client, "Sıradan")
    assert client.get("/admin/waitlist", headers=h2).status_code == 403


def test_join_page_served(client):
    r = client.get("/join")
    assert r.status_code == 200
    assert "Artora" in r.text and "waitlist" in r.text.lower() or "listeye" in r.text.lower()
