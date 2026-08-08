"""Aşama 1: görsel küçültme + Premium model katmanı (2026-08-08).

Maliyetin çoğu girdi (görsel) tarafında; küçültme token'ı belirgin azaltıyor.
Premium katmanı ise ödeme yapan kullanıcıya güçlü modeli veriyor.
"""

import io

import pytest
from PIL import Image

from app.ai.images import prepare_for_model


def _png(w: int, h: int, mode: str = "RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(mode, (w, h), (200, 180, 160) if mode == "RGB" else None).save(
        buf, format="PNG"
    )
    return buf.getvalue()


def _size(raw: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(raw)) as im:
        return im.size


def test_large_image_is_downscaled(client):
    """Telefon çizimi (1600x2000) → en uzun kenar 1024."""
    out = prepare_for_model(_png(1600, 2000))
    w, h = _size(out)
    assert max(w, h) == 1024
    assert (w, h) == (819, 1024)  # oran korunuyor


def test_downscaling_shrinks_payload_substantially(client):
    """Asıl amaç: base64 gövdesi küçülsün (token maliyeti)."""
    raw = _png(1600, 2000)
    out = prepare_for_model(raw)
    assert len(out) < len(raw) / 2, f"{len(raw)} → {len(out)}"


def test_small_image_is_not_upscaled(client):
    """Küçük görsel büyütülmez — yoksa boşuna token harcanır."""
    out = prepare_for_model(_png(400, 300))
    assert _size(out) == (400, 300)


def test_transparent_png_gets_white_background(client):
    """Şeffaf çizim JPEG'e çevrilirken siyah zemine düşmemeli — model boş alanı
    gölge sanar. Kâğıt beklenen arka plan: beyaz."""
    buf = io.BytesIO()
    Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(buf, format="PNG")
    out = prepare_for_model(buf.getvalue())
    with Image.open(io.BytesIO(out)) as im:
        assert im.mode == "RGB"
        assert im.getpixel((25, 25)) == (255, 255, 255)


def test_broken_image_passes_through(client):
    """Küçültme ASLA akışı bozmaz: açılamayan veri aynen geçer."""
    junk = b"bu bir gorsel degil"
    assert prepare_for_model(junk) == junk


def test_downscaling_can_be_disabled(client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "ai_image_max_edge", 0)
    raw = _png(1600, 2000)
    assert prepare_for_model(raw) == raw


# ---------- Premium model katmanı ----------


@pytest.fixture
def openrouter(monkeypatch):
    from app.ai.factory import get_ai_provider
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", "openrouter")
    monkeypatch.setattr(s, "openrouter_api_key", "test-key")
    monkeypatch.setattr(s, "openrouter_model", "free/model")
    get_ai_provider.cache_clear()
    yield s
    get_ai_provider.cache_clear()


def test_premium_uses_premium_model(client, openrouter, monkeypatch):
    from app.ai.factory import get_ai_provider

    monkeypatch.setattr(openrouter, "openrouter_premium_model", "paid/model")
    assert get_ai_provider(premium=False)._model == "free/model"
    assert get_ai_provider(premium=True)._model == "paid/model"


def test_premium_falls_back_when_unset(client, openrouter):
    """Ayar boşsa Premium normal modele düşer — ödeme yapan kullanıcının
    analizi hiç çalışmamasındansa farksız çalışsın."""
    from app.ai.factory import get_ai_provider

    assert get_ai_provider(premium=True)._model == "free/model"
