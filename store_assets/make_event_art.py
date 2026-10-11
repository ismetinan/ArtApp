#!/usr/bin/env python3
"""In-App Event görselleri: "Kurucu Çizer" kampanyası (2026-10).

Metinsiz (Apple etkinlik adını kartın üstüne kendisi yazar). Uygulamanın mor
paleti + ortada rozet (roket) + çevresinde çizim motifleri (fırça, kalem,
parıltı). İki boyut üretir:
  event_card_1920x1080.png     (16:9, Event Card Media)
  event_details_1080x1920.png  (9:16, Event Details Page Media)

Önemli öğeler merkezde tutulur — kart farklı ekranlarda kenarlardan kırpılabiliyor.

Kullanım: python3 store_assets/make_event_art.py [çıktı_klasörü]
"""

import math
import random
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICONS = {"rocket": 0xF055D, "brush": 0xE113, "pencil": 0xE21A, "palette": 0xE46B,
         "sparkle": 0xE0B7, "star": 0xE5F9}


def _icon_font(size: int) -> ImageFont.FreeTypeFont:
    flutter = shutil.which("flutter")
    d = Path(flutter).resolve().parent.parent / "bin/cache/artifacts/material_fonts"
    return ImageFont.truetype(str(d / "MaterialIcons-Regular.otf"), size)


def _radial_bg(w: int, h: int) -> Image.Image:
    """Merkezde açık mor, kenarlara doğru koyu mor ışıma."""
    small = Image.new("RGB", (w // 8, h // 8))
    cx, cy = small.width / 2, small.height * 0.48
    maxd = math.hypot(cx, cy)
    inner, outer = (124, 92, 214), (28, 18, 62)
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            t = min(1.0, math.hypot(x - cx, y - cy) / maxd) ** 0.9
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(inner, outer))
    return small.resize((w, h), Image.BICUBIC)


def _glyph(canvas, name, center, size, color, angle=0, blur=0):
    font = _icon_font(size)
    ch = chr(ICONS[name])
    layer = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = d.textbbox((0, 0), ch, font=font)
    d.text((size - (box[0] + box[2]) / 2, size - (box[1] + box[3]) / 2), ch, font=font, fill=color)
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(layer, (round(center[0] - size), round(center[1] - size)))


def _sketch_lines(canvas, rng, count, scale):
    """Arka planda karakalem eskiz izi gibi ince, yarı saydam eğriler."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = canvas.size
    for _ in range(count):
        x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        pts = []
        ang = rng.uniform(0, math.tau)
        for i in range(12):
            ang += rng.uniform(-0.35, 0.35)
            x0 += math.cos(ang) * 28 * scale
            y0 += math.sin(ang) * 28 * scale
            pts.append((x0, y0))
        d.line(pts, fill=(255, 255, 255, rng.randint(14, 32)), width=max(2, round(3 * scale)))
    canvas.alpha_composite(layer)


def make(w: int, h: int, seed: int = 7) -> Image.Image:
    rng = random.Random(seed)
    s = min(w, h) / 1080
    canvas = _radial_bg(w, h).convert("RGBA")
    _sketch_lines(canvas, rng, 26, s)

    cx, cy = w / 2, h * 0.48
    r = 250 * s

    # Rozet: dış ışıma + altın halka + mor disk
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - r * 1.45, cy - r * 1.45, cx + r * 1.45, cy + r * 1.45],
                                 fill=(255, 205, 120, 90))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(70 * s)))
    d = ImageDraw.Draw(canvas)
    d.ellipse([cx - r * 1.08, cy - r * 1.08, cx + r * 1.08, cy + r * 1.08], fill=(246, 196, 92))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(103, 80, 164))
    d.ellipse([cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86],
              outline=(255, 255, 255, 60), width=round(6 * s))
    _glyph(canvas, "rocket", (cx, cy), round(300 * s), (255, 255, 255, 255), angle=0)

    # Çevre motifleri: fırça, kalem, palet, parıltılar. Konumlar merkeze göre
    # (dx, dy) birimi rozet yarıçapı; yatay kartta yanlara daha çok yayılır.
    wide = w > h
    spread = 1.55 if wide else 1.0
    motifs = [
        ("brush", (-2.0 * spread, 0.55) if wide else (-1.45, 1.15), 150, 20, 230),
        ("pencil", (2.0 * spread, 0.5) if wide else (1.45, 1.1), 140, -10, 230),
        ("sparkle", (1.55, -1.45), 120, 0, 255),
        ("sparkle", (-1.55, -1.35), 80, 0, 210),
        ("star", (1.75 * spread, -0.45), 64, 0, 200),
        ("star", (-1.5, 1.6), 56, 0, 180),
    ]
    if wide:
        motifs += [
            ("palette", (-3.3, -0.85), 120, -12, 170),
            ("sparkle", (3.25, -0.95), 90, 0, 190),
            ("star", (-3.0, 1.35), 48, 0, 150),
            ("star", (3.4, 1.25), 52, 0, 150),
        ]
    else:
        motifs += [
            ("palette", (0.0, 2.1), 120, 0, 170),
            ("star", (1.5, -0.2), 50, 0, 160),
        ]
    for name, (dx, dy), size, rot, alpha in motifs:
        _glyph(canvas, name, (cx + dx * r, cy + dy * r), round(size * s),
               (255, 236, 200, alpha), angle=rot)
    return canvas.convert("RGB")


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, (w, h) in {"event_card_1920x1080.png": (1920, 1080),
                         "event_details_1080x1920.png": (1080, 1920)}.items():
        make(w, h).save(out / name, optimize=True)
        print(out / name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "store_assets/in_app_event")
