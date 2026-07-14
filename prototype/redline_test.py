#!/usr/bin/env python3
"""Faz 0 doğrulama prototipi (production kodu DEĞİL).

AI redline analizinin farklı çizim stillerinde (manga / realist / karikatür)
tutarlı çalışıp çalışmadığını test eder. Backend'deki gerçek sağlayıcı
adaptörlerini kullanır — yani burada doğrulanan prompt'lar üretimde de aynıdır.

Kullanım:
    cd backend && .venv/bin/python ../prototype/redline_test.py            # mock ile kuru koşu
    AI_PROVIDER=gemini GEMINI_API_KEY=... .venv/bin/python ../prototype/redline_test.py

Çıktı: prototype/output/ altına bulgu işaretli overlay PNG'ler + konsola özet.
"""

import asyncio
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROTO_DIR = Path(__file__).parent
sys.path.insert(0, str(PROTO_DIR.parent / "backend"))

from app.ai import RedlineResult, get_ai_provider, guard_redline  # noqa: E402

STYLES = ["manga", "realist", "karikatur"]
SEVERITY_COLORS = {"dusuk": "#f0c020", "orta": "#f07020", "yuksek": "#e02020"}


def render_overlay(image_path: Path, result: RedlineResult, out_path: Path) -> None:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    r = max(8, min(img.size) // 40)
    for i, f in enumerate(result.findings, 1):
        cx, cy = f.x * img.width, f.y * img.height
        color = SEVERITY_COLORS[f.severity.value]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
        draw.text((cx + r + 4, cy - r), str(i), fill=color)
    img.save(out_path)


async def main() -> None:
    provider = get_ai_provider()
    out_dir = PROTO_DIR / "output"
    out_dir.mkdir(exist_ok=True)

    total = 0
    for style in STYLES:
        style_dir = PROTO_DIR / "test_images" / style
        images = sorted(
            p for p in style_dir.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        if not images:
            print(f"[{style}] görsel yok — {style_dir} klasörüne çizim ekleyin")
            continue
        for path in images:
            result = guard_redline(
                await provider.redline_analysis(path.read_bytes(), "genel teknik değerlendirme")
            )
            out_path = out_dir / f"{style}-{path.stem}-redline.png"
            render_overlay(path, result, out_path)
            total += 1
            print(f"\n=== [{style}] {path.name} → {out_path.name}")
            print("Güçlü yönler:", "; ".join(result.strengths_tr))
            for i, f in enumerate(result.findings, 1):
                print(f"  {i}. ({f.skill_axis.value}, {f.severity.value}) {f.message_tr}")
                print(f"     Öneri: {f.suggestion_tr}")
            print("Genel:", result.overall_comment_tr)

    print(f"\nToplam {total} görsel analiz edildi.")
    if total:
        print("Değerlendirme kriteri: bulgular stiller arasında tutarlı ve stil-tarafsız mı?")
        print("(Manga çizimine 'gerçekçi değil' tarzı geri bildirim = önyargı işareti)")


if __name__ == "__main__":
    asyncio.run(main())
