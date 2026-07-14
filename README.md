# ArtApp

Kendi kendine öğrenen çizerler için AI destekli, oyunlaştırılmış mentor platformu.
Vizyon ve faz planı için `CLAUDE.md`'ye bak. **Aktif faz: Faz 1 (MVP).**

## Yapı

```
backend/     FastAPI + PostgreSQL — API, AI katmanı (backend/app/ai/)
mobile/      Flutter uygulaması (Mentorlar | Dersler | Profil)
prototype/   Faz 0 doğrulama script'i (redline tutarlılık testi)
docs/        Wireframe'ler
```

## Hızlı başlangıç

```bash
# 1. Veritabanı + Redis
docker compose up -d

# 2. Backend
cd backend
cp ../.env.example .env          # AI_PROVIDER=mock ile anahtarsız çalışır
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000/docs

# 3. Testler
.venv/bin/python -m pytest

# 4. Mobil uygulama
cd ../mobile
flutter run                      # Android emülatörü: --dart-define=API_BASE=http://10.0.2.2:8000
```

## AI sağlayıcı değiştirme

`.env` içinde `AI_PROVIDER=mock` (varsayılan, anahtarsız) veya `AI_PROVIDER=gemini`
(+ `GEMINI_API_KEY`, ücretsiz: https://aistudio.google.com). Yeni sağlayıcı eklemek
için `backend/app/ai/base.py` arayüzünü uygulayan tek dosya + `factory.py`'a bir satır.

## Faz 0 doğrulama

`prototype/test_images/README.md` içindeki kontrol listesine göre çizim ekle, sonra:

```bash
cd backend
AI_PROVIDER=gemini GEMINI_API_KEY=... .venv/bin/python ../prototype/redline_test.py
```
