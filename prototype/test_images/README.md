# Faz 0 Test Görselleri

Bu klasöre kendi (veya arkadaşlarının) çizimlerini koy — görseller gitignore'da,
repo'ya girmez.

## Kontrol listesi

- [ ] `manga/` — en az 2 manga/anime tarzı çizim
- [ ] `realist/` — en az 2 gerçekçi tarz çizim (figür, portre veya natürmort)
- [ ] `karikatur/` — en az 2 karikatür/cartoon tarzı çizim
- [ ] Karışık seviyeler: hem başlangıç hem orta seviye örnekler olsun ki
      geri bildirimin seviyeye göre tonu gözlemlensin
- [ ] PNG veya JPG formatında

## Çalıştırma

```bash
cd backend
AI_PROVIDER=gemini GEMINI_API_KEY=anahtar .venv/bin/python ../prototype/redline_test.py
```

Sonuçlar `prototype/output/` klasörüne overlay PNG olarak düşer.

## Neye bakılacak (Faz 0 geç/kal kriteri)

1. Bulgular üç stilde de teknik olarak anlamlı mı?
2. Herhangi bir stile "yanlış stil" muamelesi var mı? (önyargı = KAL)
3. Koordinatlar gerçekten sorunlu bölgeye mi işaret ediyor?
4. Ton her örnekte yapıcı mı?
