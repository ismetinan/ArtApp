"""Demo (App Review) hesapları gerçek kullanıcılardan gizli (2026-10).

Demo hesaplar @artora.app alan adını kullanır (scripts/seed_demo.py). İçerikleri
yalnız dahili hesaplara görünür — reviewer her şeyi dolu görür, gerçek kullanıcı
hiç görmez. En kritik dal havuz eşleştirmesi: gerçek öğrencinin isteği cevap
vermeyecek demo mentora atanırsa 48 saat boşa bekler.
"""

from tests.test_mentors import _enable_market, _make_admin, _submit, _user


def _register(client, email, name="Kişi"):
    r = client.post(
        "/users/register",
        json={"email": email, "password": "GucluParola123!", "display_name": name},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _approve_mentor(client, h):
    r = client.post("/mentors/apply", json={"bio": "Mentor", "styles": ["manga"]}, headers=h)
    assert r.status_code == 200, r.text
    admin_h, _ = _user(client, "Admin")
    _make_admin(client, admin_h)
    apps = client.get("/admin/mentor-applications", headers=admin_h).json()["applications"]
    pid = apps[0]["id"]
    client.post(f"/admin/mentor-applications/{pid}/approve", headers=admin_h)
    return pid


def _share(client, h):
    sid = _submit(client, h)
    assert client.patch(
        f"/submissions/{sid}/privacy", json={"is_public": True}, headers=h
    ).status_code == 200
    return sid


def test_gallery_hides_demo_drawings_from_real_users(client):
    demo_h = _register(client, "demo@artora.app", "Demo Çizer")
    demo_sid = _share(client, demo_h)
    real_h, _ = _user(client, "Gerçek")
    real_sid = _share(client, real_h)

    real_view = {i["submission_id"] for i in client.get("/gallery", headers=real_h).json()["items"]}
    demo_view = {i["submission_id"] for i in client.get("/gallery", headers=demo_h).json()["items"]}
    assert real_view == {real_sid}
    assert demo_view == {demo_sid, real_sid}  # reviewer her şeyi görür


def test_mentor_list_and_profile_hide_demo_mentor(client, monkeypatch):
    _enable_market(monkeypatch)
    demo_h = _register(client, "demo.helper@artora.app", "Demo Mentor")
    pid = _approve_mentor(client, demo_h)
    real_h, _ = _user(client, "Öğrenci")

    assert client.get("/mentors", headers=real_h).json()["mentors"] == []
    assert client.get(f"/mentors/{pid}", headers=real_h).status_code == 404
    # Dahili hesap görür
    other_demo = _register(client, "demo@artora.app")
    assert [m["id"] for m in client.get("/mentors", headers=other_demo).json()["mentors"]] == [pid]
    assert client.get(f"/mentors/{pid}", headers=other_demo).status_code == 200


def test_pool_never_assigns_real_student_to_demo_mentor(client, monkeypatch):
    _enable_market(monkeypatch)
    _approve_mentor(client, _register(client, "demo.helper@artora.app", "Demo Mentor"))
    real_h, _ = _user(client, "Öğrenci")
    sid = _submit(client, real_h)
    r = client.post(f"/submissions/{sid}/mentor-request", json={}, headers=real_h)
    # Tek mentor demo → gerçek öğrenci için havuz boş
    assert r.status_code == 409, r.text


def test_direct_request_to_demo_mentor_is_404_for_real_user(client, monkeypatch):
    _enable_market(monkeypatch)
    pid = _approve_mentor(client, _register(client, "demo.helper@artora.app"))
    real_h, _ = _user(client, "Öğrenci")
    sid = _submit(client, real_h)
    r = client.post(
        f"/submissions/{sid}/mentor-request", json={"mentor_id": pid}, headers=real_h
    )
    assert r.status_code == 404


def test_demo_student_can_still_use_demo_mentor(client, monkeypatch):
    """App Review akışı bozulmamalı: demo öğrenci demo mentora ulaşabilir."""
    _enable_market(monkeypatch)
    _approve_mentor(client, _register(client, "demo.helper@artora.app", "Demo Mentor"))
    demo_h = _register(client, "demo@artora.app")
    sid = _submit(client, demo_h)
    r = client.post(f"/submissions/{sid}/mentor-request", json={}, headers=demo_h)
    assert r.status_code == 200, r.text


def test_every_lesson_has_a_video():
    from app.data.skill_tree import SEED_NODES

    assert all(n["resources"] for n in SEED_NODES), [
        n["id"] for n in SEED_NODES if not n["resources"]
    ]
    first = next(n for n in SEED_NODES if n["id"] == "cizgi-temelleri")
    assert first["resources"][0]["youtube_id"] == "0_AdsK8x9Lw"
