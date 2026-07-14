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

**Şu anki aktif faz: Faz 1 (Faz 0 doğrulama prototipi paralel yürüyor — `prototype/redline_test.py`, Gemini anahtarı gelince gerçek çizimlerle koşulacak)**

> AI sağlayıcı kararı (2026-07-14): Anthropic anahtarı henüz yok. Tüm AI çağrıları
> `backend/app/ai/` içindeki sağlayıcı-bağımsız arayüz üzerinden gider (`AI_PROVIDER`
> env değişkeni: `mock` | `gemini`). İlk gerçek sağlayıcı Gemini ücretsiz katmanı;
> Claude/OpenAI adaptörleri ileride tek dosyayla eklenir. Fine-tuning Faz 4 konusu.

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

- Jeton fiyatlandırması ve mentor gelir paylaşım oranı henüz belirlenmedi.
- Yetenek ağacındaki düğüm sayısı ve içerik müfredatı (hangi YouTube videoları) henüz hazır değil — bu bir içerik/uzman işi, kod işi değil.
- Mentor onay/kalite kontrol süreci (kim mentor olabilir, nasıl doğrulanır) tanımlanmadı.
- Ability Chart'taki eksenlerin (beceri kategorilerinin) kesin listesi ve skor hesaplama mantığı netleştirilmeli.
- "Gelişim Macerası" galerisindeki gizlilik ayarının varsayılan değeri (herkese açık mı, özel mi) belirlenmeli.
