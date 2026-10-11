#!/usr/bin/env python3
"""Ödev uyumu değerlendirme seti (production kodu DEĞİL, 2026-10).

Soru: "Bu çizim verilen ödevi karşılıyor mu?" kararını model ne kadar doğru
veriyor? Beklenen sonucu bilinen (görsel, ödev) çiftleri gerçek modele
gönderilir, kapı kararı (task_match >= eşik) beklentiyle karşılaştırılır.

Karşılaştırılan yapılandırmalar:
  old-lite  : eski prompt + eski şema (model tek sayı uydurur) + flash-lite
  new-lite  : yeni prompt + kontrol listesi şeması (puanı sunucu hesaplar) + flash-lite
  new-flash : yeni prompt + kontrol listesi şeması + flash

Kullanım (backend/.env içindeki OPENROUTER_API_KEY kullanılır):
    cd backend && .venv/bin/python ../prototype/task_match_eval.py [--configs new-lite,new-flash]

Çıktı: konsola özet tablo + prototype/output/task_match_eval.json (tüm yanıtlar).
Eski prompt `--old-prompts <yol>` ile verilir (git show HEAD~:backend/app/ai/prompts.py).
"""

import argparse
import asyncio
import importlib.util
import json
import sys
import time
from pathlib import Path

PROTO_DIR = Path(__file__).parent
sys.path.insert(0, str(PROTO_DIR.parent / "backend"))

from pydantic import BaseModel, Field  # noqa: E402

from app.ai.openrouter import OpenRouterProvider, _image_part  # noqa: E402
from app.ai.prompts import redline_prompt  # noqa: E402
from app.ai.schemas import RedlineFinding, TaskRedlineModelOut  # noqa: E402
from app.ai.tone_guard import guard_redline  # noqa: E402
from app.core.config import get_settings  # noqa: E402

IMAGES = PROTO_DIR / "test_images"
THRESHOLD = 50
MODELS = {"lite": "google/gemini-2.5-flash-lite", "flash": "google/gemini-2.5-flash"}


def brief(goal: str, steps: list[str], criteria: list[str]) -> str:
    """Yeni ödev biçimi (AssignmentBrief.to_text ile aynı şekil)."""
    lines = [goal, ""] + [f"{i}. {s}" for i, s in enumerate(steps, 1)]
    lines += ["", "Başarı kriterleri:"] + [f"- {c}" for c in criteria]
    return "\n".join(lines)


OFF_TASKS = {
    "kupa-3-aci": brief(
        "Basit bir objeyle farklı açılardan çizimi çalış.",
        ["Bir kupa fotoğrafı seç.", "Kupayı önden, üstten ve 3/4 açıdan üç ayrı kez çiz.",
         "Ağız ve tabandaki elipsleri yapı çizgileriyle kur."],
        ["Kupa üç ayrı çizimde var.", "Çizimler önden, üstten ve 3/4 açıdan.",
         "Elipsler yapı çizgileriyle kurulmuş."],
    ),
    "tek-nokta-oda": brief(
        "Tek kaçış noktasıyla derinlik kurmayı çalış.",
        ["Sayfaya bir ufuk çizgisi ve üzerinde bir kaçış noktası koy.",
         "Bir odayı (duvarlar, zemin, bir masa) bu noktaya giden çizgilerle çiz.",
         "Kaçış çizgilerini silme."],
        ["Ufuk çizgisi ve kaçış noktası görünür.", "Oda/mekân çizilmiş.",
         "Derinlik çizgileri tek noktada birleşiyor."],
    ),
    "deger-skalasi": brief(
        "Açık-koyu değer geçişini çalış.",
        ["Yan yana 5 kare çiz.", "Kareleri beyazdan siyaha kademeli tara.",
         "Altına basit bir küre çizip aynı değerlerle gölgelendir."],
        ["5 karelik değer skalası var.", "Değerler açıktan koyuya düzenli geçiyor.",
         "Gölgelendirilmiş bir küre var."],
    ),
}

# Görsel → (uyumlu ödev, sınır vaka ödevi | None). Sınır vaka: konu doğru ama
# ödevin bazı kriterleri bariz eksik — kapı kararı beklenmez, puan raporlanır.
ON_TASKS = {
    "karikatur/karikatur-1-sise.jpg": (
        brief("Abartıyla karakter yaratmayı çalış.",
              ["Bir karakter seç.", "Yüz ifadesini ve bir özelliğini abartarak çiz.",
               "Karakterin elinde ya da yanında bir obje olsun."],
              ["Abartılı bir karikatür karakter var.", "Yüz ifadesi belirgin.",
               "Karakterle birlikte bir obje çizilmiş."]),
        None,
    ),
    "karikatur/karikatur-2-roar.jpg": (
        brief("Çizgi film tarzında hareketli bir sahne çalış.",
              ["Bir ya da birkaç yaratık/karakter tasarla.",
               "Onları hareket halinde, ifadeli çiz.", "Sahneye ses efekti yazısı ekle."],
              ["Çizgi film tarzı yaratık/karakter var.", "Hareket ya da ifade belirgin.",
               "Ses efekti yazısı var."]),
        None,
    ),
    "karikatur/karikatur-3-sapkali.jpg": (
        brief("Bir kişinin karakteristik özelliğini abartarak portre çiz.",
              ["Bir kişi seç.", "Yüzünü ve bir aksesuarını (ör. şapka) çiz.",
               "Bir özelliği abart."],
              ["Bir kişinin portresi var.", "Aksesuar (şapka vb.) çizilmiş."]),
        None,
    ),
    "manga/manga-1-levi.jpg": (
        brief("Dinamik pozda tam boy figür çalış.",
              ["Hareket halindeki bir karakter seç.", "Tam boy, dinamik bir pozda çiz.",
               "Elinde bir nesne tutsun."],
              ["Tam boy figür var.", "Poz dinamik/hareketli.", "Figür bir nesne tutuyor."]),
        brief("Jest çizimiyle hız çalış.",
              ["30 saniyelik 10 ayrı hızlı poz çiz.", "Her pozda yalnız hareket çizgisini yakala.",
               "Detay ekleme."],
              ["En az 10 ayrı hızlı poz var.", "Pozlar basit hareket çizgileriyle.",
               "Detay yok, hızlı etüt."]),
    ),
    "manga/manga-2-el-sallayan.jpg": (
        brief("El ve yüz ifadesini birlikte çalış.",
              ["Bir karakter seç.", "El sallarken çiz; açık el net görünsün.",
               "Yüz ifadesi neşeli olsun."],
              ["Karakter el sallıyor.", "Açık el net çizilmiş.", "Yüz ifadesi görünür."]),
        None,
    ),
    "manga/manga-3-yakin-plan.jpg": (
        brief("Yakın plan yüz ve göz çizimini çalış.",
              ["Bir karakterin yüzünü yakın plan çiz.", "Gözleri detaylı işle.",
               "Saç tutamlarını ekle."],
              ["Yakın plan bir yüz var.", "Gözler detaylı.", "Saç çizilmiş."]),
        brief("Loomis yöntemiyle kafayı farklı açılardan kurmayı çalış.",
              ["Loomis kafa yapısını (küre + yan kesit) çiz.",
               "Aynı kafayı önden, profilden ve 3/4 açıdan üç kez kur.",
               "Yapı çizgilerini silme."],
              ["Üç ayrı kafa çizimi var.", "Önden, profil ve 3/4 açılar var.",
               "Loomis yapı çizgileri görünür."]),
    ),
    "realist/realist-1-kapusonlu.jpeg": (
        brief("Kumaş kıvrımlarını ve figürü çalış.",
              ["Kapüşonlu giysili bir figür seç.", "Figürü kumaş kıvrımlarıyla çiz.",
               "Gölgeleri tarama ile ver."],
              ["Kapüşonlu bir figür var.", "Kumaş kıvrımları çizilmiş.", "Tarama ile gölge var."]),
        None,
    ),
    "realist/realist-2-portre.jpeg": (
        brief("Portrede ışık-gölge çalış.",
              ["Bir portre referansı seç.", "Yüzü oranlarına dikkat ederek çiz/boya.",
               "Tek bir ışık kaynağına göre gölgelendir."],
              ["Bir portre var.", "Yüz oranları kurulmuş.", "Işık-gölge tek yönden."]),
        None,
    ),
}


class OldTaskOut(BaseModel):
    """Eski şema: model 0-100 tek sayı verir (karşılaştırma için)."""

    strengths_tr: list[str]
    findings: list[RedlineFinding]
    overall_comment_tr: str
    task_match: float = Field(description="0-100")
    task_match_comment_tr: str


def load_old_prompts(path: str):
    spec = importlib.util.spec_from_file_location("old_prompts", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cases():
    for img, (on, border) in ON_TASKS.items():
        yield img, "on", on, True
        for name, task in OFF_TASKS.items():
            yield img, f"off:{name}", task, False
        if border:
            yield img, "border", border, None


async def run_one(config, img, label, task, sem, old_mod):
    kind, model_key = config.split("-")
    provider = OpenRouterProvider(
        get_settings().openrouter_api_key, MODELS[model_key], fallback_model=""
    )
    image = (IMAGES / img).read_bytes()
    async with sem:
        t0 = time.monotonic()
        try:
            if kind == "old":
                prompt = old_mod.redline_prompt("Ders", "tr", task)
                content = [_image_part(image), {"type": "text", "text": prompt}]
                out = await provider._generate(content, OldTaskOut)
                score = max(0, min(100, round(out.task_match)))
                extra = {"comment": out.task_match_comment_tr}
            else:
                content = [_image_part(image),
                           {"type": "text", "text": redline_prompt("Ders", "tr", task)}]
                out = await provider._generate(content, TaskRedlineModelOut)
                res = guard_redline(out.to_result(), "tr")
                score = res.task_match
                extra = {
                    "desc": res.drawing_description_tr,
                    "subject": res.subject_matches,
                    "checks": [(c.criterion_tr, c.status) for c in res.task_checks or []],
                    "comment": res.task_match_comment_tr,
                    "strengths": res.strengths_tr,
                    "findings": [(f.severity.value, f.message_tr, f.suggestion_tr)
                                 for f in res.findings],
                    "overall": res.overall_comment_tr,
                    "next_step": res.next_step_tr,
                }
            return {"ok": True, "score": score, "secs": round(time.monotonic() - t0, 1), **extra}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="old-lite,new-lite,new-flash")
    ap.add_argument("--old-prompts", default="")
    args = ap.parse_args()
    configs = args.configs.split(",")
    old_mod = load_old_prompts(args.old_prompts) if args.old_prompts else None
    if any(c.startswith("old") for c in configs) and old_mod is None:
        sys.exit("old-* yapılandırması için --old-prompts gerekli")

    sem = asyncio.Semaphore(6)
    all_cases = list(cases())
    results = {}
    for config in configs:
        outs = await asyncio.gather(*[
            run_one(config, img, label, task, sem, old_mod)
            for img, label, task, _ in all_cases
        ])
        results[config] = [
            {"image": img, "label": label, "expected": exp, **o}
            for (img, label, _, exp), o in zip(all_cases, outs)
        ]

    print(f"\nKapı eşiği: task_match >= {THRESHOLD}\n")
    print(f"{'yapılandırma':12} {'doğruluk':>9} {'yanlış-geçti':>13} {'yanlış-kaldı':>13} "
          f"{'hata':>5} {'uyumlu ort.':>12} {'alakasız ort.':>14} {'sınır puanları':>16}")
    for config, rows in results.items():
        judged = [r for r in rows if r["expected"] is not None and r["ok"]]
        correct = sum((r["score"] >= THRESHOLD) == r["expected"] for r in judged)
        fp = sum(r["score"] >= THRESHOLD and not r["expected"] for r in judged)
        fn = sum(r["score"] < THRESHOLD and r["expected"] for r in judged)
        errors = sum(not r["ok"] for r in rows)
        on = [r["score"] for r in judged if r["expected"]]
        off = [r["score"] for r in judged if not r["expected"]]
        border = [r["score"] for r in rows if r["expected"] is None and r["ok"]]
        avg = lambda xs: f"{sum(xs) / len(xs):.0f}" if xs else "-"  # noqa: E731
        print(f"{config:12} {correct:>4}/{len(judged):<4} {fp:>13} {fn:>13} {errors:>5} "
              f"{avg(on):>12} {avg(off):>14} {str(border):>16}")

    out = PROTO_DIR / "output"
    out.mkdir(exist_ok=True)
    (out / "task_match_eval.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"\nTüm yanıtlar: {out / 'task_match_eval.json'}")


if __name__ == "__main__":
    asyncio.run(main())
