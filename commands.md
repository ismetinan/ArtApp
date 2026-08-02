venv/bin/uvicorn app.main:app --reload --host 0.0.0.0

fuser -k 8000/tcp

flutter run -d 4870494a --dart-define=API_BASE=http://[IP_ADDRESS]

1. Apple Developer üyeliğini bitir — kritik yol bu, doğrulama 1–7 gün sürebilir. Onay gelmeden aşağıdakilerin hiçbiri yapılamaz.

2. App Store Connect → My Apps → ➕ New App
- iOS / Artora / Türkçe / Bundle ID com.ismetinan.artapp / SKU artora-ios-001
- ➡️ Oluşunca sayısal Apple ID'yi bana ver (codemagic.yaml'daki 0000000000 yerine yazacağım).

3. App Store Connect API Key (Users and Access → Integrations → App Store Connect API → ➕, erişim App Manager)
- .p8 dosyası (yalnız bir kez indirilir, güvenli sakla) + Key ID + Issuer ID
- Bunları sadece Codemagic UI'a gir; bana ya da repoya asla girmesin.

4. Codemagic — codemagic.io → GitHub ile giriş → Add application → ArtApp → Flutter
- Team → Integrations → App Store Connect → Connect (adım 3'teki üçlü). Entegrasyon adı: CodemagicASC (yaml'daki adla birebir).
- "Use codemagic.yaml" seçili olsun → Start new build → "Artora iOS TestFlight". Sertifika/profil ilk build'de otomatik üretilir, ~15–25 dk, IPA otomatik TestFlight'a gider.

5. TestFlight → Internal Testing'e kendini ekle, gerçek iPhone'da uçtan uca dene, ekran görüntülerini burada al (6.7"; onboarding, yetenek ağacı, AI analiz, profil/ability chart, mentor listesi).

6. App Store submit → ekran görüntüleri + açıklama + App Privacy etiketleri + Age Rating + inceleme notlarına bir test hesabı (Apple misafir akışını atlayabilir) ve "Google girişi bu platformda sunulmuyor" notu. Gizlilik politikası URL'i ve uygulama içi hesap silme zaten hazır. İnceleme genelde 1–3 gün.

Adım 2'yi bitirip Apple ID'yi verdiğinde codemagic.yaml'ı güncelleyip push ediyorum — sonra build'i tetikleyebilirsin.
