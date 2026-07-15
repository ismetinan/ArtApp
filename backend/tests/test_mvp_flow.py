"""Faz 1 bitiş kriteri testi: yükle → seviye al → ağaçta ilerle → ödev → AI analiz."""

import io

PNG = (
    b"\x89PNG\r\n\x1a\n" + bytes.fromhex(
        "0000000d49484452000000010000000108060000001f15c489"
        "0000000d4944415478da63fcffff3f0300050201e2260ad90000000049454e44ae426082"
    )
)


def _png_file(name="cizim.png"):
    return (name, io.BytesIO(PNG), "image/png")


def _guest(client) -> dict:
    r = client.post("/users/guest", json={"display_name": "Test Çizer"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_full_mvp_loop(client):
    headers = _guest(client)

    # 1. Onboarding: 3 çizim → seviye + ability skorları
    r = client.post(
        "/onboarding/assess",
        files=[("files", _png_file(f"c{i}.png")) for i in range(3)],
        headers=headers,
    )
    assert r.status_code == 200
    assessment = r.json()
    assert 1 <= assessment["level"] <= 10
    assert len(assessment["ability_scores"]) == 7  # renk dahil
    assert assessment["summary_tr"]

    # 2. Yetenek ağacı: kök ders açık, önkoşullular kilitli, kaynaklar seed'li
    tree = client.get("/skill-tree", headers=headers).json()["nodes"]
    by_id = {n["id"]: n for n in tree}
    assert by_id["cizgi-temelleri"]["status"] == "available"
    assert by_id["temel-oranlar"]["status"] == "locked"
    assert by_id["cizgi-temelleri"]["resources"][0]["kind"] == "playlist"
    assert by_id["kafa-oranlari"]["resources"][0]["youtube_id"] == "wAOldLWIDSM"

    # 3. Kilitli derse ödev gönderilemez
    r = client.post(
        "/skill-tree/temel-oranlar/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 403

    # 4. Açık derse ödev → AI redline + XP
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["xp_awarded"] == 40
    # Ödev sonrası seviye, onboarding'de belirlenen başlangıç seviyesinin altına düşmemeli
    assert body["level"] >= assessment["level"]
    analysis = body["analysis"]
    assert analysis["strengths_tr"], "Ton kuralı: her analizde en az bir güçlü yön"
    for f in analysis["findings"]:
        assert 0 <= f["x"] <= 1 and 0 <= f["y"] <= 1
        assert f["suggestion_tr"], "Her bulgu uygulanabilir öneriyle gelmeli"

    # 5. Ders tamamlanınca önkoşullu ders açılır (chart ↔ dersler ilişkisi)
    tree = client.get("/skill-tree", headers=headers).json()["nodes"]
    by_id = {n["id"]: n for n in tree}
    assert by_id["cizgi-temelleri"]["status"] == "completed"
    assert by_id["temel-oranlar"]["status"] == "available"

    # 6. Aynı derse ikinci gönderim: analiz var, mükerrer XP yok
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.json()["xp_awarded"] == 0

    # 7. Profil: seviye, ability chart, Gelişim Macerası (varsayılan: özel)
    profile = client.get("/profile", headers=headers).json()
    assert profile["xp"] == (assessment["level"] - 1) * 100 + 40
    assert profile["ability_chart"]["cizgi_kalitesi"] > 0
    macera = profile["gelisim_macerasi"]
    assert len(macera) == 2
    assert all(m["is_public"] is False for m in macera)
    assert macera[0]["ai_result"]["overall_comment_tr"]

    # 8. Gizlilik değiştirilebilir
    sid = macera[0]["submission_id"]
    r = client.patch(f"/submissions/{sid}/privacy", json={"is_public": True}, headers=headers)
    assert r.json()["is_public"] is True


def test_auth_required(client):
    assert client.get("/profile").status_code in (401, 422)
    assert (
        client.get("/profile", headers={"Authorization": "Bearer gecersiz"}).status_code
        == 401
    )
