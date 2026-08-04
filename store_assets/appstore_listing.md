# Artora — App Store Connect metadata (kopyala-yapıştır)

App Store Connect → Artora → **App Store** sekmesi → sol menüde sürüm (1.0).
Alan alan aşağıdaki metinleri gir. Karakter sınırları başlıklarda yazıyor.

⚠️ Bu sürümde **uygulama içi satın alma iOS'ta kapalı** (`billingEnabled` iOS'ta
false). Metinlerde jeton satın almadan bahsedilmiyor — bahsedilirse Apple
"tanımlı ürün yok" diye sorar.

---

## 1. App Information (sürümden bağımsız)

| Alan | Değer |
|---|---|
| **Name** (30) | `Artora` |
| **Subtitle** (30) | `AI destekli çizim koçu` |
| **Primary Category** | Education |
| **Secondary Category** | Graphics & Design |
| **Content Rights** | "Contains, shows, or accesses third-party content" → **Hayır** (YouTube videoları uygulama dışında, kendi barındırdığımız içerik yok) |
| **Privacy Policy URL** | `https://artapp-production.up.railway.app/privacy` |

EN subtitle (English (U.S.) yerelleştirmesi eklersen): `AI-powered drawing coach`

---

## 2. Türkçe (birincil dil)

### Promotional Text (170) — sürüm göndermeden güncellenebilir
```
Çizimini yükle, saniyeler içinde ücretsiz AI analizi al. Yetenek ağacında ilerle,
zayıf yönlerini gör, gerektiğinde gerçek bir mentora sor.
```

### Description (4000)
```
Kendi kendine çizim mi öğreniyorsun? Artora, yıllarını yanlış yönde harcamanı engellemek için var.

Son 3 çizimini yükle; Artora'nın yapay zekâsı 7 temel beceride başlangıç seviyeni belirlesin: anatomi, perspektif, ışık-gölge, oran, çizgi kalitesi, kompozisyon ve renk. Oradan sonrasında oyunlaştırılmış bir yetenek ağacı, seni doğru sırayla ilerleyen ücretsiz video derslerden geçirir.

NASIL ÇALIŞIR

1. Son 3 çizimini yükle — AI güçlü ve zayıf yönlerini çıkarır.
2. Yetenek ağacını takip et — her düğümde özenle seçilmiş video dersler var.
3. Ödevini yükle — anında ve ücretsiz "redline" analizi al: çizimin üzerinde
   somut noktalar, neyin çalıştığı ve neyi denemen gerektiği.
4. XP kazan, seviye atla, ability chart'ının büyümesini izle.
5. AI yetmezse jetonunla ödevini gerçek bir mentora gönder.

ARTORA'YI FARKLI KILAN

• Geri bildirim her zaman yapıcı — asla kırıcı, asla cesaret kırıcı değil.
• Stil ayrımcılığı yok: manga, karikatür ya da realizm — kendi stilin içinde
  koçluk alırsın, başkasının stiline itilmezsin.
• Her gözlem uygulanabilir bir öneriyle gelir, muğlak eleştiriyle değil.
• Gelişim maceran her ödevi AI notlarıyla saklar; ne kadar yol aldığını
  gerçekten görürsün.
• Topluluk galerisinde diğer çizerlerin paylaştıklarına bak, istersen kendi
  çalışmanı paylaş.

MENTOR DESTEĞİ

Yapay zekâ analizi ücretsiz ve günlük kotayla sınırsıza yakın. Bir insana
sormak istediğinde jetonunu harcayıp ödevini mentor havuzuna gönderirsin;
onaylı bir mentor çizimine bakıp kişisel geri bildirim yazar. Her hafta
ücretsiz jeton kazanırsın.

Bulunduğun yerden başla. Her çizimle ilerle.
```

### Keywords (100 karakter, virgülle, boşluksuz)
```
çizim,resim,eskiz,anatomi,perspektif,sanat,öğren,ders,portre,karakter,manga,illüstrasyon,AI
```
(97 karakter. "Artora" ve kategori adlarını yazma — Apple zaten indeksliyor.)

### Support URL
```
https://artapp-production.up.railway.app/join
```

### What's New in This Version (4000) — 1.0 için
```
Artora'nın ilk sürümü. Çizimlerini yükle, AI'dan anında teknik geri bildirim al,
yetenek ağacında ilerle ve gerektiğinde bir mentora sor.
```

---

## 3. English (U.S.) — opsiyonel ama önerilir

### Promotional Text (170)
```
Upload a drawing, get free AI feedback in seconds. Climb the skill tree, see
your weak spots, and ask a real mentor when you need one.
```

### Description
`store_assets/store_listing_en.md` içindeki metin temel alınabilir, ancak
**"FREE DURING BETA / marketplace is coming"** bölümü artık yanlış — mentor
pazarı yayında. Onun yerine:

```
MENTOR SUPPORT

AI analysis is free with a generous daily limit. When you want a human eye,
spend a jeton to send your assignment to the mentor pool — an approved mentor
reviews your drawing and writes personal feedback. You earn free jetons weekly.
```

### Keywords (100)
```
drawing,sketch,art,anatomy,perspective,learn,lesson,portrait,character,manga,illustration,AI,tutor
```

---

## 4. App Privacy (App Store Connect → App Privacy)

"Do you or your third-party partners collect data from this app?" → **Yes**

Toplanan veriler ve işaretlenecek kutular:

| Veri türü | Kullanım | Kimliğe bağlı mı? | İzleme? |
|---|---|---|---|
| **Contact Info → Email Address** | App Functionality (hesap oluşturma/giriş) | ✔ Evet | ✗ Hayır |
| **Contact Info → Name** | App Functionality (görünen ad) | ✔ Evet | ✗ Hayır |
| **User Content → Photos or Videos** | App Functionality (çizimlerin analizi ve mentora iletimi) | ✔ Evet | ✗ Hayır |
| **User Content → Other User Content** | App Functionality (paylaşılan galeri gönderileri) | ✔ Evet | ✗ Hayır |
| **Identifiers → User ID** | App Functionality | ✔ Evet | ✗ Hayır |

**İşaretlenmeyecekler** (bu sürümde toplanmıyor):
- Purchases / Financial Info — iOS'ta satın alma kapalı
- Usage Data, Diagnostics — Crashlytics iOS'ta yapılandırılmadı
- Location, Contacts, Browsing History, Search History, Sensitive Info
- Advertising Data — reklam yok
- "Used for Tracking" — **hiçbiri** için işaretleme (ATT izni istemiyoruz)

Misafir kullanıcı için de aynı etiketler geçerli (çizim yüklüyor).

---

## 5. Age Rating

Ankette kritik cevaplar:

| Soru | Cevap |
|---|---|
| User Generated Content | **Infrequent/Mild** — kullanıcılar çizim paylaşabiliyor |
| Moderation kontrolleri (UGC seçilince sorulur) | **Evet, var** — AI ön filtre + kullanıcı bildirimi + admin gizleme |
| Violence, Sexual Content, Profanity, Horror, Alcohol/Drugs, Gambling | **None** |
| Unrestricted Web Access | **Hayır** (YouTube videoları uygulama içinde gömülü oynatılıyor, serbest tarayıcı yok) |
| Made for Kids | **Hayır** |

Beklenen sonuç: **12+**

> UGC sorusuna "None" demek yanlış olur — topluluk galerisi var; yanlış beyan
> sonradan uygulama kaldırma sebebi.

---

## 6. App Review Information

| Alan | Değer |
|---|---|
| Sign-in required | **İşaretleme** — misafir girişi tüm akışı kapsıyor |
| First / Last Name | İsmet / İnan |
| Phone | `+90...` (kendi numaran) |
| Email | `ismet17inan@gmail.com` |

**Notes:**
```
Uygulama hesap açmadan "Misafir olarak devam et" ile tam olarak kullanılabilir;
giriş bilgisi gerekmez.

Akış: Misafir girişi → 3 çizim yükle (galeriden herhangi bir çizim/eskiz olur)
→ AI seviye analizi (30-60 sn sürebilir, sunucu tarafında çalışır) → Dersler
sekmesinde yetenek ağacı → bir düğüme gir, ödev yükle → AI redline analizi.

Notlar:
- Google/Apple ile giriş bu platformda sunulmuyor; e-posta kaydı veya misafir
  girişi kullanılıyor.
- Uygulama içi satın alma bu sürümde devre dışı; mağaza ekranı erişilebilir
  değil. Jetonlar ücretsiz veriliyor (kayıtta 3 adet + haftalık 1 adet).
- Kullanıcı içeriği için üç katmanlı moderasyon var: yükleme anında AI ön
  filtresi, kullanıcı bildirim butonu, admin gizleme paneli.
- Hesap silme uygulama içinden yapılabiliyor: Profil → Hesabı Sil.
```

---

## 7. Ekran görüntüleri

Zorunlu: **6.9" iPhone** (1290×2796 ya da 1320×2868), en az 1 — pratikte 5.
iPad görüntüsü **gerekmez**: hedef iPhone-only (`TARGETED_DEVICE_FAMILY = "1"`).

### Mevcut durum (2026-08-04)

`store_assets/ioss/` içine 5 dosya kondu ama **ikisi birebir aynı** (md5 eşit)
→ elde 4 farklı kare var. Hepsi 1290×2796'ya ölçeklenip
`store_assets/ios_screenshots/` altına yazıldı:

| Dosya | İçerik | Yükleme durumu |
|---|---|---|
| `01_profil_ability_chart.png` | Profil üstü | ⚠️ tamamen boş durum |
| `02_mentorlar.png` | Mentor listesi | ⚠️ test verisi |
| `03_topluluk.png` | Topluluk galerisi | ⚠️ tek gönderi |
| `04_profil_ayarlar.png` | Ayarlar (Sign Out / Delete Account) | ❌ pazarlama karesi değil |

### Neden bu haliyle gönderilmemeli

1. **Boyut/kalite**: dosyalar WhatsApp'tan geldiği için 946×2048'e sıkıştırılmış;
   1290'a çıkarmak yazıları yumuşatıyor. Telefondan **AirDrop / iCloud / e-postaya
   "gerçek boyut" ekleyerek** aktarılırsa kayıpsız 1290×2796 gelir.
2. **Guideline 2.3.3** — ekran görüntüleri uygulamayı *kullanımda* göstermeli.
   Şu anki karelerde "Your chart will appear here", "Your journey starts here",
   `test` / `test2` / iki kez `Guest Artist` görünüyor. Bu, hem red riski hem de
   mağaza sayfasında kötü ilk izlenim.
3. **Dil uyuşmazlığı**: birincil dil Türkçe, kareler İngilizce. Türkçe
   yerelleştirmeye Türkçe kare konmalı (Profil → Dil → Türkçe ile çekilecek).
4. **Ürünün kalbi eksik**: yetenek ağacı ve AI redline analizi hiç yok — satışı
   yapan iki ekran bunlar.

### Yeniden çekim listesi (telefonda, Dil = Türkçe)

Önce misafir değil **kayıtlı hesapla** dolu bir durum oluştur (3 çizim yükle →
seviye analizi bitsin → bir ödev gönder → AI analizi gelsin). Sonra:

1. **Yetenek ağacı** (Dersler sekmesi, birkaç düğüm açılmış halde)
2. **AI redline analiz sonucu** (analiz metni görünür şekilde)
3. **Profil + ability chart** (radar grafiği dolu, Level 2+, XP > 0)
4. **Ders düğümü** (video + ödev yükleme butonu)
5. **Mentorlar listesi** (test kayıtları temizlendikten sonra)

> Mentor listesindeki `test` / `test2` / `Guest Artist` kayıtları prod veritabanında
> duruyor. Ekran görüntüsünden bağımsız olarak, yayın öncesi bunları admin
> panelinden temizlemek gerekir — gerçek kullanıcılar da bu listeyi görüyor.
