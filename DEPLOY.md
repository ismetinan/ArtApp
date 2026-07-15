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
   Test: `curl https://xxx.up.railway.app/health` → `{"status":"ok"}`.
   Migration'lar açılışta otomatik koşar, ağaç otomatik seed'lenir.

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
2. **Create app**: ArtApp, Türkçe, Uygulama (oyun değil), ücretsiz.
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
