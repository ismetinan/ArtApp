"""Güvenlik sıkılaştırma turu (2026-09).

- API dokümanları (/docs, /openapi.json) prod'da kapalı; HSTS başlığı
- Yetki (IDOR): başkasının kaydına her uç 404/403 döner
- Mentor, üstlendiği isteğin (özel) çizimini görebilir; başkası göremez
- Yüklemede EXIF/GPS meta verisi silinir; sıkıştırma bombası reddedilir
- Jetonsuz yükleme depoya dosya yazmaz (öksüz dosya / depolama suistimali)
- Admin kararları denetim kaydına düşer
"""

import io
from pathlib import Path

import pytest
from PIL import Image

from tests.test_analysis_jobs import _submit_async
from tests.test_mentors import (
    _approved_mentor,
    _enable_market,
    _make_admin,
    _submit,
    _user,
)


def _jpeg_with_gps() -> bytes:
    im = Image.new("RGB", (40, 20), (200, 30, 30))
    exif = Image.Exif()
    exif[0x0110] = "Gizli Telefon Modeli"  # Model
    exif[0x0112] = 6  # Orientation: 90° döndür
    gps = exif.get_ifd(0x8825)
    gps[1] = "N"
    gps[2] = (41.0, 1.0, 2.0)  # enlem
    out = io.BytesIO()
    im.save(out, "JPEG", exif=exif)
    return out.getvalue()


def _upload(client, h, data: bytes, name="odev.jpg"):
    return client.post(
        "/skill-tree/cizgi-temelleri/submit",
        files={"file": (name, io.BytesIO(data), "image/jpeg")},
        headers=h,
    )


# ------------------------------------------------------------------ yüzey


def test_api_docs_disabled_by_default(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404, path


def test_hsts_header(client):
    r = client.get("/health")
    assert "max-age=" in r.headers["Strict-Transport-Security"]


# ------------------------------------------------------------------- IDOR


def test_idor_across_users(client, monkeypatch):
    _enable_market(monkeypatch)
    owner_h, _ = _user(client, "Sahip")
    other_h, _ = _user(client, "Meraklı")
    sid = _submit(client, owner_h)
    job = _submit_async(client, owner_h).json()

    # Özel çizim, iş, gizlilik ayarı: başkasına 404
    assert client.get(f"/submissions/{sid}/image", headers=other_h).status_code == 404
    assert client.get(f"/analysis-jobs/{job['job_id']}", headers=other_h).status_code == 404
    r = client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": True}, headers=other_h
    )
    assert r.status_code == 404
    # Başkasının çizimini mentora gönderemez
    r = client.post(f"/submissions/{sid}/mentor-request", json={}, headers=other_h)
    assert r.status_code == 404
    # Özel çizim şikayet edilemez (varlığı bile sızmaz)
    r = client.post(
        f"/submissions/{sid}/report", json={"reason": "spam"}, headers=other_h
    )
    assert r.status_code == 404


def test_idor_mentor_requests(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Öğrenci")
    stranger_h, _ = _user(client, "Yabancı")
    sid = _submit(client, student_h)
    rid = client.post(
        f"/submissions/{sid}/mentor-request", json={}, headers=student_h
    ).json()["request_id"]

    # Yabancı ne cevaplayabilir ne puanlayabilir
    r = client.post(
        f"/mentor-requests/{rid}/feedback", json={"feedback_text": "x"}, headers=stranger_h
    )
    assert r.status_code == 403
    r = client.post(f"/mentor-requests/{rid}/rating", json={"rating": 1}, headers=stranger_h)
    assert r.status_code == 404
    # Mentor, öğrencinin yerine puan veremez
    r = client.post(f"/mentor-requests/{rid}/rating", json={"rating": 5}, headers=mentor_h)
    assert r.status_code == 404


def test_admin_endpoints_forbidden_for_users(client, monkeypatch):
    _enable_market(monkeypatch)
    h, _ = _user(client, "Sıradan")
    for path in (
        "/admin/stats",
        "/admin/reports",
        "/admin/mentor-applications",
        "/admin/analytics/overview",
        "/admin/analytics/users",
    ):
        assert client.get(path, headers=h).status_code == 403, path
    assert client.post("/admin/reports/1/hide", headers=h).status_code == 403


# ------------------------------------------------------- mentor görsel erişimi


def test_assigned_mentor_can_view_private_drawing(client, monkeypatch):
    _enable_market(monkeypatch)
    mentor_h = _approved_mentor(client, monkeypatch)
    student_h, _ = _user(client, "Öğrenci")
    stranger_h, _ = _user(client, "Yabancı")
    sid = _submit(client, student_h)
    # İstekten önce mentor bile göremez
    assert client.get(f"/submissions/{sid}/image", headers=mentor_h).status_code == 404
    client.post(f"/submissions/{sid}/mentor-request", json={}, headers=student_h)
    assert client.get(f"/submissions/{sid}/image", headers=mentor_h).status_code == 200
    # İsteğin tarafı olmayan hâlâ göremez
    assert client.get(f"/submissions/{sid}/image", headers=stranger_h).status_code == 404


# ------------------------------------------------------------ yükleme güvenliği


def test_exif_gps_stripped_and_orientation_applied(client):
    raw = _jpeg_with_gps()
    with Image.open(io.BytesIO(raw)) as im:
        assert im.getexif().get(0x0110) == "Gizli Telefon Modeli"  # ön koşul

    h, _ = _user(client, "Fotoğrafçı")
    r = _upload(client, h, raw)
    assert r.status_code == 200, r.text
    stored = client.get(f"/submissions/{r.json()['submission_id']}/image", headers=h).content
    with Image.open(io.BytesIO(stored)) as im:
        exif = im.getexif()
        assert not exif.get_ifd(0x8825)  # GPS yok
        assert 0x0110 not in exif  # cihaz modeli yok
        # Orientation=6 piksellere uygulandı: 40×20 → 20×40
        assert im.size == (20, 40)
    assert b"Gizli Telefon" not in stored


def test_clean_image_stored_byte_identical(client):
    """Meta verisi olmayan görsel yeniden sıkıştırılmaz (kalite kaybı yok)."""
    from tests.test_mentors import PNG

    h, _ = _user(client, "Temiz")
    r = _upload(client, h, PNG, name="odev.png")
    stored = client.get(f"/submissions/{r.json()['submission_id']}/image", headers=h).content
    assert stored == PNG


def test_decompression_bomb_rejected(client):
    im = Image.new("L", (7000, 7000), 0)  # 49 MP > 40 MP sınırı, dosyası küçük
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    assert len(out.getvalue()) < 8 * 1024 * 1024
    h, _ = _user(client, "Bombacı")
    r = _upload(client, h, out.getvalue(), name="bomb.png")
    assert r.status_code == 422


def test_no_orphan_files_without_jetons(client, monkeypatch, tmp_path):
    """Jetonsuz kullanıcı yükleme yaptığında 402 alır ve depoya DOSYA YAZILMAZ."""
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "jeton_ai_economy_enabled", True)
    h, data = _user(client, "Jetonsuz")
    from app import db as db_module
    from app.models.tables import User

    with db_module.SessionLocal() as db:
        u = db.get(User, data["id"])
        u.jeton_balance = 0
        u.jeton_paid_balance = 0
        # haftalık tabana tamamlama bu test boyunca tetiklenmesin
        from datetime import datetime, timezone

        u.free_jeton_last_grant = datetime.now(timezone.utc)
        db.commit()

    drawings = Path(s.storage_dir) / "drawings"
    before = set(drawings.glob("*")) if drawings.exists() else set()
    for endpoint in ("/skill-tree/cizgi-temelleri/submit-async", "/free-analysis-async"):
        from tests.test_mentors import PNG

        r = client.post(
            endpoint, files={"file": ("a.png", io.BytesIO(PNG), "image/png")}, headers=h
        )
        assert r.status_code == 402, (endpoint, r.status_code, r.text)
    after = set(drawings.glob("*")) if drawings.exists() else set()
    assert after == before


# ----------------------------------------------------------- denetim kaydı


@pytest.mark.parametrize("decision", ["hide", "dismiss"])
def test_admin_report_decision_audited(client, decision):
    from sqlalchemy import select

    from app import db as db_module
    from app.models.tables import AdminAuditLog

    admin_h, admin = _user(client, "Yönetici")
    _make_admin(client, admin_h)
    owner_h, _ = _user(client, "Paylaşan")
    sid = _submit(client, owner_h)
    client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=owner_h)
    reporter_h, _ = _user(client, "Şikayetçi")
    client.post(f"/submissions/{sid}/report", json={"reason": "spam"}, headers=reporter_h)

    assert client.post(f"/admin/reports/{sid}/{decision}", headers=admin_h).status_code == 200
    with db_module.SessionLocal() as db:
        row = db.execute(select(AdminAuditLog)).scalar_one()
        assert (row.admin_id, row.action, row.target_type, row.target_id) == (
            admin["id"], f"report_{decision}", "submission", sid
        )

    # Admin hesabını silse de kayıt kalır (admin_id NULL)
    assert client.delete("/users/me", headers=admin_h).status_code == 200
    with db_module.SessionLocal() as db:
        row = db.execute(select(AdminAuditLog)).scalar_one()
        assert row.admin_id is None
