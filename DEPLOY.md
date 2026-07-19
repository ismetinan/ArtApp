# ArtApp — Go-Live Rehberi (Faz 1 Beta)

Kod tarafı hazır. Aşağıdaki konsol adımları senin hesaplarınla yapılmalı;
her adımın çıktısını (URL/ID/anahtar) Claude'a ver, gerisini o bağlar.

---

## 1. Railway (backend hosting) — ~$5/ay

1. https://railway.app → GitHub ile kayıt ol, repo'yu bağla.
2. **New Project → Deploy from GitHub repo** → bu repo → *Root Directory:* `backend`
   (Dockerfile otomatik algılanır).
3. **+ New → Database → PostgreSQL** ekle. Railway `DATABASE_URL` değişkenini verir —
   ama bizim format `postgresql+psycopg://` ister: servisin Variables sekmesinde
   `DATABASE_URL` değerini Postgres eklentisinden kopyalayıp başını
   `postgresql://` → `postgresql+psycopg://` olarak düzelt.
4. Backend servisinin **Variables** sekmesine ekle:
   ```
   AI_PROVIDER=openrouter
   OPENROUTER_API_KEY=<anahtarın>
   OPENROUTER_MODEL=google/gemma-4-26b-a4b-it:free
   OPENROUTER_FALLBACK_MODEL=nvidia/nemotron-nano-12b-v2-vl:free
   GOOGLE_CLIENT_ID=<adım 3'teki WEB client ID>
   AI_DAILY_LIMIT=10
   STORAGE_BACKEND=s3
   S3_ENDPOINT=<adım 2'deki R2 endpoint>
   S3_BUCKET=artapp-drawings
   S3_ACCESS_KEY=<R2 token access key>
   S3_SECRET_KEY=<R2 token secret>
   SENTRY_DSN=<opsiyonel>
   ```
5. **Settings → Networking → Generate Domain** → `https://xxx.up.railway.app`.
   ⚠️ Domain'in **target port'u**, Railway'in enjekte ettiği `PORT` ile eşleşmeli
   (bizim deployda 8080 çıktı; deploy loglarında "Uvicorn running on ...:PORT"
   satırından görülür). Eşleşmezse edge "connection refused" → 502 döner.
   Test: `curl https://xxx.up.railway.app/health` → `{"status":"ok"}`.
   Migration'lar açılışta otomatik koşar, ağaç otomatik seed'lenir.
   Not: uvicorn `--host 0.0.0.0` kalmalı; `::` asyncio'da v6only bağlanır ve
   Railway edge'in IPv4 bağlantıları reddedilir.

## 2. Cloudflare R2 (çizim depolama) — ücretsiz (10 GB)

1. https://dash.cloudflare.com → R2 Object Storage → **Create bucket**: `artapp-drawings`.
2. **Manage R2 API Tokens → Create API Token**: Object Read & Write, sadece bu bucket.
3. Not al: Access Key ID, Secret Access Key, endpoint
   (`https://<account_id>.r2.cloudflarestorage.com`).

## 3. Google Cloud Console (Google Sign-In) — ücretsiz

1. https://console.cloud.google.com → yeni proje: "ArtApp".
2. **APIs & Services → OAuth consent screen**: External, uygulama adı ArtApp,
   e-postan; test kullanıcılarına kendi e-postanı ekle.
3. **Credentials → Create Credentials → OAuth client ID** — İKİ tane:
   - **Web application** → adı "ArtApp Backend". Çıkan client ID = `GOOGLE_CLIENT_ID`
     (backend) ve `GOOGLE_SERVER_CLIENT_ID` (Flutter build).
   - **Android** → paket adı `com.ismetinan.artapp`, SHA-1:
     - Debug (telefonda `flutter run` için):
       `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android | grep SHA1`
     - Release (Play build'i için):
       `keytool -list -v -keystore ~/keystores/artapp-release.jks -alias artapp | grep SHA1`
     - Play'e yükledikten sonra: Play Console → Setup → App signing'deki
       **Play App Signing SHA-1**'i de üçüncü bir Android client olarak ekle
       (Play, uygulamayı kendi anahtarıyla yeniden imzalar).

## 4. Release build (yerel komut)

```bash
cd mobile
~/development/flutter/bin/flutter build appbundle \
  --dart-define=API_BASE=https://xxx.up.railway.app \
  --dart-define=GOOGLE_SERVER_CLIENT_ID=<web-client-id>.apps.googleusercontent.com
# Çıktı: build/app/outputs/bundle/release/app-release.aab
```

> İmza anahtarı: `~/keystores/artapp-release.jks` + `mobile/android/key.properties`.
> **Bu iki dosyayı yedekle (örn. şifre kasası + harici disk).** Anahtar kaybolursa
> uygulama güncellenemez. Asla commit etme (gitignore'da).

## 5. Google Play Console — $25 (tek seferlik)

1. https://play.google.com/console → geliştirici hesabı aç.
2. **Create app**: **Artora** (marka adı; paket adı `com.ismetinan.artapp` kalır), Türkçe, Uygulama (oyun değil), ücretsiz.
3. **Testing → Closed testing → Create track** → `app-release.aab` yükle →
   test kullanıcılarının e-postalarını ekle → paylaşılan katılım linkini dağıt.
4. Zorunlu formlar (App content):
   - **Privacy policy URL**: `https://xxx.up.railway.app/privacy`
   - **Data safety**: e-posta adresi + kullanıcı içeriği (görseller) toplanır;
     aktarımda şifreli (HTTPS); kullanıcı silme talep edebilir (uygulama içi
     Profil → Hesabı Sil); üçüncü tarafla paylaşım: AI analizi için görsel
     işlenir (OpenRouter), reklam/pazarlama yok.
   - **Account deletion**: uygulama içi yol var (Profil → Hesabı Sil) +
     `/privacy` sayfasındaki e-posta.
   - İçerik derecelendirme anketi: şiddet/kumar yok → "Herkes".

## 6. Yayın öncesi son kontroller

- [ ] Faz 0 doğrulaması: `prototype/test_images/{manga,realist,karikatur}/` içine
      gerçek çizimler koy → Claude `prototype/redline_test.py`'yi koşup stil
      tarafsızlığını raporlasın (CLAUDE.md kapısı).
- [ ] Railway URL'siyle telefonda uçtan uca akış: Google ile giriş → onboarding
      (7 eksenli chart) → ders kaynakları → ödev → gerçek AI redline → galeri →
      hesap silme.
- [ ] Redeploy sonrası çizimlerin durduğunu doğrula (R2 çalışıyor demektir).
- [ ] OpenRouter'a ~$10 kredi (opsiyonel ama önerilir): ücretsiz model günlük
      limitini belirgin yükseltir; güncel koşullar openrouter.ai'da.

## Faz 2'ye not (ödemeler)

Jeton satışı **uygulama içinde** yapılacaksa Google Play Billing zorunlu
(dijital ürün; Stripe uygulama içinde kullanılamaz, %15-30 komisyon).
Stripe Connect, mentorlara **ödeme dağıtımı** (payout) için kullanılır.
Bu ayrım Faz 2 planlanırken masada olmalı.

## 7. Faz 2 rollout (mentor pazarı, ödemesiz beta)

1. Kod deploy edilince migration otomatik koşar: mentor tabloları + herkese
   3 hoşgeldin jetonu backfill'i. Flag kapalıyken tüm mentor uçları 404 döner.
2. **Flag'i aç**: Railway → Variables → `MENTOR_MARKET_ENABLED=true` → redeploy.
3. **Admin hesabı** (mentor başvurularını onaylamak için, bir kez):
   Railway → Postgres → Data/Query sekmesinde:
   `UPDATE users SET is_admin = true WHERE email = 'SENIN-EPOSTAN';`
4. Onay akışı: admin hesabıyla `GET /admin/mentor-applications` →
   `POST /admin/mentor-applications/{id}/approve`. (Beta'da uygulama içi admin
   ekranı yok; curl/HTTP istemcisiyle yapılır.)
5. Test senaryosu: bir hesap mentor olur (başvur + onayla), ikinci hesap bir
   ödevin redline ekranından "Mentora sor — 1 jeton" ile istek atar; mentor
   panelinden cevap yazılır; öğrenci puanlar. 48 saat cevapsız istek otomatik
   iade edilir.

## 8. Firebase / Push bildirimleri (FCM)

1. https://console.firebase.google.com → **Proje oluştur: Artora** (Google
   Analytics kapatılabilir).
2. Projeye **Android uygulaması ekle**: paket adı `com.ismetinan.artapp`
   (SHA gerekmez) → **google-services.json** dosyasını indir →
   `mobile/android/app/google-services.json` olarak koy (gizli değildir,
   commit edilir; dosya gelene kadar build FCM'siz çalışır).
3. Firebase → Proje ayarları → **Service accounts** → *Generate new private
   key* → inen JSON dosyasının TAM içeriğini kopyala → Railway → Variables →
   `FIREBASE_SERVICE_ACCOUNT_JSON` değişkenine yapıştır (GİZLİ — asla commit
   etme). Lokal test için aynı değer `backend/.env`'e de konabilir.
4. Yeni AAB build + dahili test. Doğrulama: bayrak açıkken öğrenci mentor
   isteği atınca mentorun telefonuna, mentor cevap yazınca öğrenciye bildirim
   düşmeli (uygulama öndeyken SnackBar, kapalıyken sistem bildirimi).

## 9. Play Billing (jeton paketleri + Premium abonelik)

Hibrit model: dersler herkese ücretsiz; jeton paketleri (tüketilebilir) +
`premium_monthly` aboneliği (ayda 10 hediye jeton + günlük AI limiti 10→50).
Kod `BILLING_ENABLED` bayrağı arkasında — kapalıyken uçlar 404, UI gizli.

**Sıra önemli: önce billing izinli AAB (0.5.0+7) Play'e yüklenmeli** — ürün
tanımlama menüleri ancak billing izni içeren bir sürüm yüklendikten sonra açılır.

1. **AAB yükle**: 0.5.0+7'yi dahili test kanalına yükle (in_app_purchase
   eklentisi `com.android.vending.BILLING` iznini kendisi ekler).
2. **Ürünleri tanımla**: Play Console → Para kazanma (Monetize) →
   - Uygulama içi ürünler → Ürün oluştur: kimlikler **`jeton_5`**, **`jeton_15`**,
     **`jeton_40`** (kimlikler birebir böyle olmalı — backend kataloğuyla eşleşir).
     Ad/açıklama serbest, fiyatı sen belirle, hepsini **Etkinleştir**.
   - Abonelikler → Abonelik oluştur: kimlik **`premium_monthly`**, temel plan:
     aylık, otomatik yenilenen. Fiyatı belirle, etkinleştir.
3. **API erişimi (sunucu doğrulaması)**: Google Cloud Console'da (Play'e bağlı
   projede) **Google Play Android Developer API**'yi etkinleştir → bir service
   account oluştur → JSON anahtar indir. Play Console → Kullanıcılar ve
   izinler → Kullanıcı davet et → service account e-postasına **Finansal
   veriler + Sipariş yönetimi** izni ver. JSON'un TAM içeriğini Railway →
   `PLAY_SERVICE_ACCOUNT_JSON` değişkenine yapıştır (GİZLİ — asla commit etme).
4. **Bayrağı aç**: Railway → `BILLING_ENABLED=true` → redeploy.
5. **Lisans testçileri** (gerçek para gitmesin): Play Console → Ayarlar →
   Lisans testi → test hesaplarının e-postalarını ekle. Bu hesaplar test
   kartıyla "satın alır", ücret çekilmez.
6. **Telefon testi**: Profil → jeton çipine dokun → mağaza açılır →
   jeton paketi al → bakiye artmalı (profilde ve `jeton_transactions`'ta
   `purchase` satırı) → mentor isteğinde harca. Premium al → profil rozetinde
   "Premium" görünmeli, günlük AI limiti artmalı. Jeton yetersizken mentor
   isteği → SnackBar'da "Jeton Al" aksiyonu çıkmalı.

Not: abonelik yenilemeleri Pub/Sub'sız, uygulama açılışında lazy doğrulanır;
iptal edilen abonelik dönem sonunda kendiliğinden düşer.
