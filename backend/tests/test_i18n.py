"""i18n: dil seçimi, mesaj kataloğu, AI çıktı dili ve ağaç çevirileri."""

import io

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _png_file(name="test.png"):
    return (name, io.BytesIO(PNG), "image/png")


def _auth(client, language=""):
    body = {"display_name": "Test"}
    if language:
        body["language"] = language
    r = client.post("/users/guest", json=body)
    assert r.status_code == 200
    return r.json(), {"Authorization": f"Bearer {r.json()['token']}"}


def test_guest_language_from_body_and_header(client):
    data, _ = _auth(client, language="en")
    assert data["language"] == "en"

    r = client.post(
        "/users/guest",
        json={"display_name": "X"},
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    assert r.json()["language"] == "en"

    r = client.post("/users/guest", json={"display_name": "X"})
    assert r.json()["language"] == "tr"  # başlık yoksa varsayılan


def test_language_patch_and_validation(client):
    _, headers = _auth(client)
    r = client.patch("/users/me/language", json={"language": "en"}, headers=headers)
    assert r.status_code == 200 and r.json()["language"] == "en"

    r = client.patch("/users/me/language", json={"language": "fr"}, headers=headers)
    assert r.status_code == 422


def test_error_messages_follow_user_language(client):
    _, headers = _auth(client, language="en")
    # EN kullanıcı: ders bulunamadı hatası İngilizce dönmeli
    r = client.post("/skill-tree/yok-boyle-ders/submit", files={"file": _png_file()}, headers=headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Lesson not found"

    # Girişsiz istek: Accept-Language'e göre 401 mesajı
    r = client.get("/profile", headers={"Accept-Language": "en"})
    assert r.json()["detail"] == "No session found"
    r = client.get("/profile")
    assert r.json()["detail"] == "Oturum bulunamadı"


def test_ai_output_language(client):
    # EN kullanıcının redline analizi İngilizce (mock sağlayıcı dil bilir)
    _, headers = _auth(client, language="en")
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers
    )
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    assert "keep going" in analysis["overall_comment_tr"]
    # Ders bağlamı da İngilizce başlıkla geçmeli
    assert "Line Fundamentals" in analysis["overall_comment_tr"]

    _, headers_tr = _auth(client)
    r = client.post(
        "/skill-tree/cizgi-temelleri/submit", files={"file": _png_file()}, headers=headers_tr
    )
    assert "devam et" in r.json()["analysis"]["overall_comment_tr"].lower()
    assert "Çizgi Temelleri" in r.json()["analysis"]["overall_comment_tr"]


def test_tree_titles_localized(client):
    _, headers = _auth(client, language="en")
    nodes = {n["id"]: n for n in client.get("/skill-tree", headers=headers).json()["nodes"]}
    assert nodes["cizgi-temelleri"]["title"] == "Line Fundamentals"
    assert nodes["cizgi-temelleri"]["description"].startswith("Warm-up")

    _, headers_tr = _auth(client)
    nodes = {n["id"]: n for n in client.get("/skill-tree", headers=headers_tr).json()["nodes"]}
    assert nodes["cizgi-temelleri"]["title"] == "Çizgi Temelleri"


def test_tone_guard_english_fallback():
    from app.ai import RedlineFinding, RedlineResult, Severity, SkillAxis, guard_redline

    result = RedlineResult(
        strengths_tr=[],
        findings=[
            RedlineFinding(
                skill_axis=SkillAxis.ANATOMI,
                x=0.5,
                y=0.5,
                severity=Severity.ORTA,
                message_tr="This hand anatomy is terrible.",
                suggestion_tr="Study hand construction.",
            )
        ],
        overall_comment_tr="Keep going!",
    )
    guarded = guard_redline(result, language="en")
    assert "terrible" not in guarded.findings[0].message_tr.lower()
    assert "room to grow" in guarded.findings[0].message_tr
    assert guarded.strengths_tr == [
        "Finishing this piece and sharing it is a valuable step in itself."
    ]
