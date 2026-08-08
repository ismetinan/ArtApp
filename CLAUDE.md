# PROJE: Kendi Kendine Öğrenen Çizerler için AI Destekli Gamified Mentor Platformu

Bu dosya, Claude Code'un bu proje üzerinde çalışırken referans alacağı ana bağlam dosyasıdır.
Her yeni oturumda bu dosyayı oku ve kararlarını buradaki vizyon, mimari ve faz önceliklerine göre al.

---

## 1. VİZYON

Dünyadaki kendi kendine eğiten (self-taught) bağımsız çizerlerin resimde gelişirken
yıllarını yanlış yönde harcamasını engellemek. Bunu üç bileşeni tek platformda birleştirerek yapıyoruz:

1. **Oyunlaştırılmış müfredat** — Yetenek Ağacı üzerinden ilerleyen, kaliteli, sıralı bir öğrenme yolu.
2. **Anlık ve etik AI teknik analizi** — Öğrencinin yüklediği her ödeve ücretsiz, yapıcı, redline (kırmızı çizgi) tarzı geri bildirim.
3. **Küresel insan mentor pazar yeri** — Jeton karşılığı havuzdan rastgele veya seçerek mentor desteği.

Hedef kitle teknik olarak deneyimsiz, motivasyonu kırılgan olabilecek bireysel çizerler.
Bu yüzden **ton her zaman yapıcı, asla aşağılayıcı olmamalı** — bu prensip UI metninden AI prompt'larına kadar her katmanda geçerli.

---

## 2. SİSTEM AKIŞI (Kullanıcı Perspektifi)

1. **Seviye Belirleme**: Öğrenci son 3 çizimini yükler → sistem başlangıç seviyesini otomatik belirler.
2. **Yetenek Ağacı & Yönlendirme**: Anatomi, perspektif vb. temellerdeki istatistik çıkarılır → zayıf alanlara göre ağaçtaki uygun derslere yönlendirilir.
3. **Çekirdek Döngü**: Öğrenci düğümdeki YouTube videosunu izler → ödevi yükler → anlık ve ücretsiz AI redline analizi alır.
4. **Havuza Dayalı Mentorluk**: AI yeterli hissettirmezse → 1 jeton karşılığı ödev havuzdaki rastgele müsait mentora gider.
5. **Seçmeli Mentorluk (Premium)**: Öğrenci 3 jeton karşılığı profil/portfolyosuna bakarak istediği mentoru doğrudan seçer.

---

## 3. FAZLI ROADMAP (Claude Code bu sırayı takip etmeli)

Claude Code, kullanıcı aksini belirtmedikçe **bir sonraki fazın işlerine başlamadan önceki fazı tamamlamalı ve test edilebilir halde bırakmalıdır.**

### Faz 0 — Doğrulama (kod öncesi / minimal kod)
- AI redline analizinin farklı çizim stillerinde (manga, realist, karikatür) tutarlı çalışıp çalışmadığını test eden bir **script/prototip** (production kodu değil).
- Yetenek ağacı veri modelinin taslağı (düğüm, önkoşul, XP mantığı).
- Çıktı: Faz 0 "gitmiyor" derse mimari değişebilir — Claude Code bunu esnek tutmalı.

### Faz 1 — MVP (Çekirdek Döngü)
Kapsam: Onboarding + sabit yetenek ağacı + AI redline döngüsü + gamification (XP/seviye/rozet).
Kapsam DIŞI: Mentor pazarı, jeton harcama akışı (jeton bakiyesi altyapısı kurulabilir ama kullanılmaz).
Bitiş kriteri: Bir kullanıcı uçtan uca "yükle → seviye al → yetenek ağacında ilerle → ödev yükle → AI analiz al" akışını sorunsuz tamamlayabilmeli.

### Faz 2 — Mentorluk Pazarı
Kapsam: Havuza dayalı rastgele mentorluk, mentor onboarding/onay akışı, mentor paneli, ödeme altyapısı (jeton satın alma + mentor gelir paylaşımı), rating sistemi.
Bitiş kriteri: Bir öğrenci 1 jeton harcayıp ödevini havuzdaki bir mentora gönderebilmeli, mentor geri bildirim verebilmeli.

### Faz 3 — Premium & Kişiselleştirme
Kapsam: Seçmeli mentorluk (3 jeton, doğrudan seçim), mentor arama/filtreleme, dinamik/kişiselleştirilmiş yetenek ağacı yönlendirmesi, topluluk galerisi.

### Faz 4 — Ölçekleme
Kapsam: Çoklu dil desteği, bölgesel mentor havuzları, AI modelinin kendi veriyle ince ayarı, düzenli etik/önyargı denetimi.

**Şu anki aktif faz: Faz 3. Faz 2 canlıda test edildi (mentor akışı uçtan uca çalışıyor).
Faz 3'ten tamamlananlar: seçmeli mentorluk (3 jeton) + mentor arama + uygulama içi admin
paneli + Play Billing kodu (`BILLING_ENABLED` bayrağıyla açılacak — bkz. DEPLOY.md §9).
Müşteri geri bildirimi paketi eklendi (2026-07-19): skora göre ders atlama
(`SKIP_UNLOCK_SCORE=60`), tavsiye edilen ders + "kendi kursunla ilerle" notu, AI ödev
üretimi (obje/farklı açılar), teknik AI dili, serbest çizim analizi (ücretsiz 1/hafta,
Premium sınırsız), waitlist sayfası (`/join`), seviye yol haritası.
Topluluk galerisi eklendi (2026-07-19, 4. sekme "Topluluk": herkese açık paylaşılan
çizimler) — **Faz 3 kapsamı tamamlandı**; dinamik ağaç yönlendirmesinin ilk hali skor
atlama + öneriyle karşılandı, derinleştirme Faz 4'le birlikte değerlendirilir.
Faz 0 doğrulaması TAMAMLANDI (2026-07-18): 8 gerçek çizimle (manga/realist/karikatür)
OpenRouter üzerinde koşuldu, stil tarafsızlığı GEÇTİ — bkz. `prototype/FAZ0_RAPOR.md`.**

> **Ekonomi kararı (2026-08-08) — jeton = AI, mentorluk ücretsiz + bağış.**
> Eski model (jeton = mentor parası, altın/ücretsiz ayrımı, mentor gelir paylaşımı)
> **terk edildi**: mentora para ödemek ödeme aracılığı lisansı, mentor sözleşmesi,
> stopaj, IBAN/KYC toplama ve chargeback telafisi demekti. Yeni model:
>
> - **Jeton = AI kullanım birimi.** Haftada `WEEKLY_JETON_FLOOR` (3) ücretsiz;
>   **birikmez**, her hafta tabana tamamlanır. Satın alınan jetonun süresi dolmaz.
>   Fiyatlar: redline 1, serbest analiz 1, seviye belirleme 0, ödev üretimi 0.
> - **Premium = hız + kalite, hacim değil**: güçlü/paralı AI modeli
>   (`OPENROUTER_PREMIUM_MODEL`) + yüksek haftalık taban (25). Aylık jeton yığını
>   **vermez** — "birikmez" kuralını delerdi.
> - **Mentorluk tamamen ücretsiz.** Spam'i para değil kota tutuyor: aynı anda
>   3 açık istek, aynı mentora 24 saatte bir, mentor başına 5 açık istek tavanı.
> - **Mentora para = uygulama dışı, %100 mentora giden isteğe bağlı bağış.**
>   Artora komisyon almaz, para akışına girmez. Apple §3.2.1'in üç şartı
>   pazarlıksız: tamamen isteğe bağlı, %100 alıcıya, **uygulamada hiçbir şeyi
>   açmıyor** (rozet/öncelik/sıralama etkisi YOK). Link beyaz listeli + admin
>   onaylı (`services/donations.py`); serbest metinde IBAN yasak.
> - **Jeton hukuken "elektronik para" olmamalı**: nakde çevrilemez, kullanıcılar
>   arası devredilemez, yalnız uygulama içinde geçerli. Bu üç kural bozulmamalı
>   ("arkadaşına jeton hediye et" gibi bir özellik ikincisini kırar).
>
> Tümü `JETON_AI_ECONOMY_ENABLED` bayrağı arkasında; kapalıyken davranış eski
> modelle birebir aynı. **iOS'ta AÇMA** — `billingEnabled` iOS'ta zorla false
> (mağaza yok), açılırsa kullanıcı haftalık taban bitince kilitlenir. iOS IAP
> tamamlanana kadar yalnız Android. Detay: DEPLOY.md §10.
>
> Ücretlendirme (2026-07-19'dan devam): dersler her katmanda ücretsiz (içerik
> YouTube; ders paywall'u bilinçli reddedildi). Gelir: jeton paketleri
> (`jeton_5/15/40`, tüketilebilir IAP) + `premium_monthly` aboneliği. Doğrulama
> sunucuda (`services/billing.py`, Play Developer API).

> AI sağlayıcı kararı (güncel 2026-07-15): Anthropic anahtarı henüz yok. Tüm AI
> çağrıları `backend/app/ai/` içindeki sağlayıcı-bağımsız arayüz üzerinden gider
> (`AI_PROVIDER` env değişkeni: `mock` | `gemini` | `openrouter`). Aktif canlı
> sağlayıcı: **OpenRouter** (ücretsiz anahtar, OpenAI-uyumlu API, ücretsiz vision
> modelleri; model `OPENROUTER_MODEL` ile seçilir).
>
> **Gemini 401'i DÜZELTİLDİ (teşhis, 2026-08-08):** Bu bir Google hatası değil,
> yanlış kimlik bilgisi tipi. `.env`'deki `GEMINI_API_KEY` `AQ.` ile başlıyor —
> bu bir **ephemeral token** (Live API için, kısa ömürlü), API anahtarı değil.
> Gerçek Gemini API anahtarı `AIza` ile başlar. Canlı API `401
> ACCESS_TOKEN_TYPE_UNSUPPORTED` döndürüyor, mesaj birebir bunu söylüyor.
> Çözüm: Google AI Studio → "Get API key" → **Create API key** (ya da Cloud
> Console → Credentials → API key + "Generative Language API" etkin). Yine de
> **acil değil**: canlı sağlayıcı OpenRouter ve önerilen premium model
> (`google/gemini-2.5-flash`) OpenRouter üzerinden gidiyor — Google anahtarı
> hiç gerekmiyor.
>
> Claude/OpenAI adaptörleri ileride tek dosyayla eklenir. Fine-tuning
> Faz 4 konusu. Prompt'lar sağlayıcı-ortak: `backend/app/ai/prompts.py`.
>
> **Model katmanı (Aşama 1, 2026-08-08):** `get_ai_provider(premium=...)`;
> Premium abone `OPENROUTER_PREMIUM_MODEL`'i alır, ayar boşsa sessizce normal
> modele düşer. Modele giden her görsel `ai/images.py` ile en uzun kenarı
> `AI_IMAGE_MAX_EDGE` (1024) olacak şekilde küçültülüp JPEG'e çevrilir —
> gerçek çizim üzerinde ölçüldü: **görsel token 4266 → 1118 (3,8× azalma)**.

---

## 4. TECH STACK

| Katman | Teknoloji | Not |
|---|---|---|
| Mobil | Flutter | Yetenek ağacı gibi custom/canvas-yoğun UI için tercih edildi |
| Backend | Python (FastAPI) | AI pipeline'ıyla aynı dilde, entegrasyon kolaylığı |
| Veritabanı | PostgreSQL | Kullanıcı, ilerleme, jeton işlemleri |
| Cache/Kuyruk | Redis + Celery | Havuz eşleştirme, AI analiz kuyruğu, rate limiting |
| Depolama | Cloudflare R2 / S3 | Çizim yüklemeleri |
| AI Sağlayıcı | Anthropic Claude API (fallback: OpenAI) | Seviye belirleme + redline analizi |
| Pose/edge tespiti | MediaPipe / OpenPose (opsiyonel, Faz 1 sonrası değerlendirilecek) | Teknik ölçüm + VLM yorumlama hibrit yaklaşımı için |
| Video | YouTube Data API | Kendi video barındırma yok, telif riski yok |
| Ödeme | Stripe (+ Stripe Connect) | Jeton satışı + mentor ödemeleri |
| Bildirim | Firebase Cloud Messaging | Push bildirimleri |
| Gerçek zamanlı | WebSocket / Socket.io | Mentor eşleştirme anlık durumu |
| Analitik | Mixpanel / Amplitude | Retention ve düğüm bazlı takılma analizi |
| Hata izleme | Sentry | — |

---

## 5. AI REDLINE ANALİZİ — TEKNİK YAKLAŞIM

Bugünkü VLM'ler piksel üzerine doğrudan çizim yapamıyor. İki olası yaklaşım:

1. **Metin + koordinat tabanlı** (Faz 1 için önerilen): Model "sol omuz, x:120 y:340 civarı perspektif bozuk" formatında yapılandırılmış çıktı verir → backend bunu SVG/canvas overlay'e çevirir.
2. **Hibrit** (Faz 2+ için değerlendirilebilir): MediaPipe/OpenPose gibi açık kaynak modellerle teknik ölçüm çıkarılır, VLM sadece yorumlama katmanında kullanılır.

AI prompt'larında her zaman şu kurallara uyulmalı:
- Ton yapıcı, asla aşağılayıcı değil.
- Somut, uygulanabilir öneriler (soyut eleştiri değil).
- Kültürel/stilistik önyargı olmamalı (örn. sadece Batı realist stilini "doğru" kabul etmemeli).

---

## 6. ÇALIŞMA PRENSİPLERİ (Claude Code için)

- Her faz kendi içinde çalışır ve test edilebilir bir teslimat üretmeli; bir sonraki faza geçmeden önce kullanıcıdan onay iste.
- Yeni bir modül/özellik eklerken önce bu dosyadaki fazlı kapsamla çelişip çelişmediğini kontrol et.
- Jeton ekonomisi, ödeme ve mentor eşleştirme gibi para/güven içeren akışlarda ekstra test/hata kontrolü uygula.
- AI analiz çıktısı kullanıcıya gösterilmeden önce ton kontrolünden geçmeli (bkz. Bölüm 5).
- Kod tabanını faz bazlı feature flag'lerle yönetmek (örn. mentor pazarı Faz 1'de kapalı) ileride geçişleri kolaylaştırır.

---

## 7. UI/UX WIREFRAME NOTLARI

Aşağıdaki ekranlar kullanıcının elle çizdiği taslaklardan çıkarılmıştır. Ham çizimler
`docs/wireframes/` klasöründe duruyor — Claude Code görsel referans olarak bunlara bakabilir:

- `docs/wireframes/wireframe-01-dersler-mentor-liste.png`
- `docs/wireframes/wireframe-02-profil-sekmesi.png`
- `docs/wireframes/wireframe-03-onboarding-tabbar-detay.png`

> Bu dosyaları repo'ya eklerken yukarıdaki `docs/wireframes/` yoluna koy; bu CLAUDE.md
> içindeki referanslar o yolu varsayıyor. Görsel var: bkz. wireframe-01, wireframe-02, wireframe-03.

Bu çizimler **nihai UI değil**, yapısal niyeti gösteren taslaklar. Görsel tasarım
(`frontend-design` prensipleri, renk, tipografi) bu yapının üzerine ayrıca kurulacak.

### 7.1 Ana Navigasyon

Alt sekme çubuğu (tab bar): **Mentorlar | Dersler | Profil**.
Not: Derslere geçiş hem doğrudan tab bar'dan hem de Profil ekranındaki Ability Chart
üzerinden (bir düğüme tıklayarak) yapılabilir olmalı — yani Ability Chart aynı zamanda
bir navigasyon bileşeni.

### 7.2 Onboarding Akışı (4 ekran, sırayla)

1. **Hoş Geldin**: Giriş yap / Kayıt ol / Misafir olarak devam et seçenekleri.
2. **3 Resim Belirle**: Kamera ile çekme veya cihazdan dosya seçme.
3. **Analiz Bekleme**: Yüklenen 3 resmin AI tarafından inceleniyor olduğunu gösteren
   loading/spinner ekranı ("resimler inceleniyor").
4. **Değerlendirme Sonucu**: Analiz çıktısının liste/checkbox halinde özetlendiği
   ("belirlendi" işaretli) sonuç ekranı — başlangıç seviyesinin kullanıcıya ilk sunumu.

Bu akışın çıktısı doğrudan Bölüm 2'deki "Seviye Belirleme" adımını besler.

### 7.3 Profil Ekranı

- Üstte avatar + sayısal seviye rozeti (örn. "2. Seviye").
- **Ability Chart**: Radar/örümcek ağı grafiği — temel becerileri (anatomi, perspektif,
  ışık-gölge vb.) görselleştirir. Grafikteki her eksen/köşe **tıklanabilir** ve ilgili
  yetenek ağacı dersine yönlendirir (chart = hem görselleştirme hem navigasyon).
- Chart'ın altında opsiyonel olarak oranların yazılı/sayısal hali gösterilebilir
  (örn. "0/70" formatında bir beceri skoru).
- **"Gelişim Macerası"** bölümü: Kullanıcının yüklediği ödev resimleri 3'lü gruplar
  halinde, her biri kendi AI notlarıyla eşleştirilmiş şekilde kronolojik listelenir.
  Kullanıcı bu resimleri herkese açık ya da özel (serbest) paylaşabilir — bu bir
  gizlilik ayarı olarak modellenmeli.

### 7.4 Dersler (Yetenek Ağacı) Ekranı

- Düğüm (node) tabanlı yapı; düğümler birbirine sarmal/organik bir örgüyle bağlı
  (klasik doğrusal liste değil, ağaç/graf görünümü).
- Her düğümde: YouTube video + "ders sor" (soru sorma) aksiyonu + ödev yükleme akışı.
- Ability Chart ↔ Dersler arasındaki ilişki çift yönlü olmalı: chart'tan derse
  gidilebildiği gibi, bir dersi tamamlamak da ilgili chart eksenini güncellemeli.

### 7.5 Mentor Listesi Ekranı

- Filtreleme: öğrencinin ilgilendiği özelleşmiş resim/stil türünde uzman mentorları
  bulabilmesi için stil bazlı filtre.
- Her mentor kartında: mentorun notları/yorumları (opsiyonel), mentorun öne çıkardığı
  örnek bir eseri, kısa biyografi.

### 7.6 Mentor Profil Ekranı (bir mentora tıklanınca açılır)

- Mentor adı + profil görseli.
- Rozetler (opsiyonel — örn. "Top Mentor", "Anatomi Uzmanı" gibi başarı rozetleri).
- "Soru sor" butonu (havuz/seçmeli mentorluk akışını burada tetikler).
- Mentorun portfolyo galerisi.

---

## 8. AÇIK SORULAR (Kullanıcının netleştirmesi gereken)

- ~~Mentor gelir paylaşım oranı~~ → ÇÖZÜLDÜ (2026-08-08): **gelir paylaşımı yok.**
  Mentorluk ücretsiz; mentora ödeme yalnız uygulama dışı, %100 mentora giden
  isteğe bağlı bağışla. Artora komisyon almıyor ve para akışına girmiyor.
- Jeton **fiyatlandırması** (paket başına TL) hâlâ belirlenmedi. Belirlemeden önce
  `OPENROUTER_PREMIUM_MODEL` paralı bir modele geçmeli ve gerçek token maliyeti
  ölçülmeli; fiyat maliyet + mağaza kesintisi (%15-30) üzerine kurulmalı.
- ~~İçerik müfredatı hazır değil~~ → ÇÖZÜLDÜ (2026-07-15): kullanıcı kaynakları
  `art_sources.md`'de derledi; 7 eksende 16 düğümlük ağaç `backend/app/data/skill_tree.py`
  ile seed'leniyor. Eksik: `temel-oranlar` kaynağı + bozuk bir playlist linki (bkz.
  art_sources.md "Açık noktalar").
- ~~Mentor onay/kalite kontrol süreci~~ → ÇÖZÜLDÜ (2026-08-08): başvuru uygulama
  içinde kalıyor (portfolyo kullanıcının kendi galerisinden — en güçlü sinyal) ve
  **örnek kritik testi** eklendi: aday kendi çizimine en az 200 karakterlik yapıcı
  bir kritik yazıyor, admin kararını buna bakarak veriyor. Mentor kurallarının
  kabulü zorunlu; ret sonrası 14 gün tekrar başvuru beklemesi var.
- Ability Chart eksenleri (2026-07-15): anatomi, perspektif, ışık-gölge, oran,
  çizgi kalitesi, kompozisyon, renk — 7 eksen. Skor hesaplama mantığının ince ayarı açık.
- "Gelişim Macerası" galerisindeki gizlilik ayarının varsayılan değeri (herkese açık mı, özel mi) belirlenmeli.
