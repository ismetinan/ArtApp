# Müfredat Kaynakları (art_sources)

Kullanıcının derlediği YouTube kaynakları. Başlıklar oEmbed ile doğrulandı ve her
kaynak yetenek ağacındaki bir düğüme eşlendi (`backend/app/data/skill_tree.py` —
uygulama açılışında upsert edilir; buradaki tablo o eşlemenin belgesidir).

| Kaynak | Tür | Yazar | Ağaç düğümü |
|---|---|---|---|
| [Art Fundamentals! The correct order.](https://youtube.com/playlist?list=PLxLnscStGPB8cra3LkxHBSXEIhw2D2Q5i) | Playlist | Braydon G. | cizgi-temelleri |
| [Art fundamentals #1: Shapes and forms](https://youtube.com/playlist?list=PLDHJ4RxK-8Tgt-AmgLSdkgdhjL_RS5wrE) | Playlist | Tamistrash Rodriguez | sekil-ve-form |
| [Learning Perspective](https://youtube.com/playlist?list=PLtG4P3lq8RHFSW-SgbBpo3k-xq9H_tdE6) | Playlist | Proko | tek-nokta-perspektif, iki-nokta-perspektif |
| [1H ACADEMY LESSON for STUDENT has no MONEY](https://youtu.be/jF0JPyxQ_3Y) | Video | Mmmmonexx | figur-oranlari |
| [Quickly Draw Heads with the Loomis Method - Part 1](https://youtu.be/wAOldLWIDSM) | Video | Proko | kafa-oranlari |
| [How to draw heads with Loomis Method](https://youtu.be/A6KMT4Potss) | Video | Draw like a Sir | kafa-oranlari |
| [ELEMENTS OF CHARACTER: Gesture, Forms, and Animation](https://youtu.be/xGhYfLQWbp0) | Video | moderndayjames | jest-cizimi |
| [PROKO ANATOMY TUTORIALS](https://youtube.com/playlist?list=PLg3tq-SuqiTlyL1pZDwNxSnCTGBZOiHvn) | Playlist | Sol Ossas (Proko derlemesi) | temel-anatomi |
| [Proko Portrait Drawing Fundamentals](https://youtube.com/playlist?list=PLR2KBLDDnZz0pHBiiyrqlOB3FU-W5XX1k) | Playlist | tullao1979 (Proko derlemesi) | portre |
| [5H CLASS](https://youtu.be/onSVS3AsQB4) | Video | Mmmmonexx | portre |
| [Go From Flat to Realistic Shading! Here's How](https://youtu.be/MyrySvbuhsk) | Video | Proko | isik-mantigi |
| [All About Value in Art: Light and Dark](https://youtu.be/fw5kamqbWnk) | Video | Mr. New's Art Class | isik-mantigi |
| [Understanding Value and Drawing Value Scales](https://youtu.be/qNawqTqUrP0) | Video | Mr. New's Art Class | deger-calismasi |
| [Essential Values for Painting, Lighting and Design](https://youtu.be/BTYGWfiZnMA) | Video | Marco Bucci | deger-calismasi |
| [What makes a great composition?](https://youtu.be/sopLk4Czp6M) | Video | Ian Roberts | temel-kompozisyon |
| [Composition in Art Explained](https://youtu.be/VwUZ3PivD6I) | Video | Art with Flo | temel-kompozisyon |
| [COMPOSITION - 3 RULES I Wish I Knew When I Started](https://youtu.be/vsW_Ams5RSk) | Video | Florent Farges | ileri-kompozisyon |
| [5 AMAZING Composition Tricks that Always Work](https://youtu.be/LITy81Feo4c) | Video | Florent Farges | ileri-kompozisyon |
| [My Top 10 Composition Tips for artists](https://youtu.be/JuEkb6FNptE) | Video | Tyler Edlin | ileri-kompozisyon |
| [Color Marco Bucci](https://youtube.com/playlist?list=PL002hNYqg1VjoRaboVhLbbCPR_0i2xUxV) | Playlist | BirchedDoors (Bucci derlemesi) | renk-temelleri |
| [10 Minutes to Better Painting Series](https://youtube.com/playlist?list=PLLmXZMqb_9sbNLM83NrM005vRQHw1yTKn) | Playlist | Marco Bucci | boyama |
| [Painting Tutorials / Demos](https://youtube.com/playlist?list=PLLmXZMqb_9sZbJOiJeq17nScRV0uo6ZQe) | Playlist | Marco Bucci | boyama |

## Açık noktalar

- ⚠️ Orijinal listedeki `PLXY6FC0h64ts` playlist bağlantısı bozuk/kesik görünüyor
  (oEmbed onu Proko'nun "Drawing Dynamic Creatures" videosuna çözüyor). Doğru
  playlist'i yeniden kopyalayıp buraya eklersen ağaca alırız.
- `temel-oranlar` düğümünün henüz kaynağı yok — temel ölçü/oran konulu bir video
  önerisi gerekiyor.
- Yeni kaynak ekleme akışı: bu tabloya satır ekle → `skill_tree.py`'de ilgili düğümün
  `resources` listesine işle → backend'i yeniden başlat (upsert otomatik).
