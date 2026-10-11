#!/usr/bin/env python3
"""App Store pazarlama ekran görüntüsü üretici (2026-10).

Ham ekran görüntüsünü (iOS ya da Android) alır:
  1. Üst durum çubuğunu ve alt gezinme çubuğunu kırpar. Apple, mağaza
     görsellerinde başka platforma ait arayüz görürse reddedebiliyor; saat/pil
     de dikkat dağıtıyor.
  2. Renkli arka plan + büyük başlık + alt başlık üzerine, yuvarlatılmış köşeli
     ve gölgeli "ekran" olarak yerleştirir.
  3. App Store'un istediği boyutlarda kaydeder: 6.9" (1290x2796), 6.5" (1284x2778).

Kullanım:
    python3 store_assets/make_screenshots.py store_assets/screenshots.json

screenshots.json:
    {
      "out_dir": "store_assets/appstore_v12",
      "shots": [
        {"file": "store_assets/android_raw/redline_light.png", "theme": "light",
         "title": "Çizimine anında\\nAI geri bildirimi", "subtitle": "...",
         "crop_top": 0.035, "crop_bottom": 0.03}
      ]
    }
crop_top / crop_bottom: görüntü yüksekliğinin oranı (varsayılan 0.035 / 0.03).
crop_end: ekranın kaçta kaçına kadar kullanılacağı (uzun ekranı kısaltmak için, ops.).
"""

import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZES = {"6.9_inch_1290x2796": (1290, 2796), "6.5_inch_1284x2778": (1284, 2778)}

# Marka rengi: uygulamanın seed rengi 0xFF6750A4 (Material mor)
THEMES = {
    "light": {
        "bg_top": (238, 232, 255), "bg_bottom": (214, 202, 250),
        "title": (40, 24, 82), "subtitle": (86, 70, 128), "frame": (255, 255, 255),
    },
    "dark": {
        "bg_top": (44, 30, 86), "bg_bottom": (18, 14, 32),
        "title": (245, 240, 255), "subtitle": (200, 188, 235), "frame": (30, 28, 36),
    },
}


def _font_dir() -> Path | None:
    flutter = shutil.which("flutter")
    if flutter:
        d = Path(flutter).resolve().parent.parent / "bin/cache/artifacts/material_fonts"
        if d.exists():
            return d
    return None


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    d = _font_dir()
    name = {"black": "Roboto-Black.ttf", "medium": "Roboto-Medium.ttf"}[weight]
    if d and (d / name).exists():
        return ImageFont.truetype(str(d / name), size)
    fallback = "DejaVuSans-Bold.ttf" if weight == "black" else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{fallback}", size)


def _gradient(size, top, bottom) -> Image.Image:
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        g.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize((w, h))


def _rounded(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *im.size], radius=radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def _draw_centered(draw, text, font, y, width, fill, spacing) -> int:
    """Çok satırlı metni ortalar; bittiği y'yi döner."""
    for line in text.split("\n"):
        box = draw.textbbox((0, 0), line, font=font)
        w, h = box[2] - box[0], box[3] - box[1]
        draw.text(((width - w) / 2 - box[0], y - box[1]), line, font=font, fill=fill)
        y += h + spacing
    return y


def compose(shot: dict, size: tuple[int, int]) -> Image.Image:
    W, H = size
    theme = THEMES[shot.get("theme", "light")]
    raw = Image.open(shot["file"]).convert("RGB")

    # 1) Platform çubuklarını kırp
    rh = raw.height
    top = round(rh * shot.get("crop_top", 0.035))
    bottom = round(rh * (1 - shot.get("crop_bottom", 0.03)))
    if "crop_end" in shot:
        bottom = min(bottom, round(rh * shot["crop_end"]))
    screen = raw.crop((0, top, raw.width, bottom))

    canvas = _gradient(size, theme["bg_top"], theme["bg_bottom"]).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # 2) Başlık + alt başlık
    s = W / 1290
    y = round(150 * s)
    y = _draw_centered(draw, shot["title"], _font("black", round(104 * s)), y, W,
                       theme["title"], round(22 * s))
    if shot.get("subtitle"):
        y += round(24 * s)
        y = _draw_centered(draw, shot["subtitle"], _font("medium", round(48 * s)), y, W,
                           theme["subtitle"], round(14 * s))

    # 3) Ekran: genişliğin ~%82'si, alt kenardan taşar (yaygın mağaza stili)
    y += round(70 * s)
    sw = round(W * 0.82)
    sh = round(screen.height * sw / screen.width)
    screen = screen.resize((sw, sh), Image.LANCZOS)
    radius = round(64 * s)
    bezel = round(14 * s)
    frame = Image.new("RGB", (sw + 2 * bezel, sh + 2 * bezel), theme["frame"])
    frame = _rounded(frame, radius + bezel)
    frame.alpha_composite(_rounded(screen, radius), (bezel, bezel))

    x = (W - frame.width) // 2
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x, y + round(24 * s), x + frame.width, y + frame.height + round(24 * s)],
        radius=radius + bezel, fill=(0, 0, 0, 110),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(round(40 * s))))
    canvas.alpha_composite(frame, (x, y))
    return canvas.convert("RGB")


def main(config_path: str) -> None:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    out = Path(cfg["out_dir"])
    for folder, size in SIZES.items():
        (out / folder).mkdir(parents=True, exist_ok=True)
        for i, shot in enumerate(cfg["shots"], 1):
            name = shot.get("name") or Path(shot["file"]).stem
            path = out / folder / f"{i:02d}_{name}.png"
            compose(shot, size).save(path, optimize=True)
            print(path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "store_assets/screenshots.json")
