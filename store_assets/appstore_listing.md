# Artora — App Store Connect metadata (kopyala-yapıştır)

App Store Connect → Artora → **App Store** sekmesi → sol menüde sürüm (1.0).
Alan alan aşağıdaki metinleri gir. Karakter sınırları başlıklarda yazıyor.

⚠️ Bu sürümde **uygulama içi satın alma iOS'ta kapalı** (`billingEnabled` iOS'ta
false). Metinlerde jeton satın almadan bahsedilmiyor — bahsedilirse Apple
"tanımlı ürün yok" diye sorar.

✅ **Metinler YENİ ekonomiye göre yazıldı** (jeton = AI kullanım birimi,
mentorluk ücretsiz). Bu metinlerle göndermek için sunucuda
`JETON_AI_ECONOMY_ENABLED=true` OLMALI — açıklama ile uygulamanın davranışı
uyuşmazsa Apple reddeder.

Satın alma açıkken ayrıca:
- **App Privacy'ye `Purchases` eklenmeli**
- **EULA alanına** `https://artapp-production.up.railway.app/terms` (jetonun
  nakde çevrilemezliği ve bağış kuralları orada beyan ediliyor)

---

## 1. App Information (sürümden bağımsız)

| Alan | Değer |
|---|---|
| **Name** (30) | `Artora` |
| **Subtitle** (30) | `AI destekli çizim koçu` |
| **Primary Category** | Education |
| **Secondary Category** | Graphics & Design |
| **Content Rights** | "Contains, shows, or accesses third-party content" → **Evet**, sonra "gerekli haklara sahibim" kutusunu işaretle. Uygulama hem YouTube videolarına yönlendiriyor hem de kullanıcı çizimlerini gösteriyor → "Hayır" demek yanlış beyan olur. |
| **Privacy Policy URL** | `https://artapp-production.up.railway.app/privacy` |
| **EULA** (App Store Connect → App Information, opsiyonel alan) | `https://artapp-production.up.railway.app/terms` — jeton kuralları (nakde çevrilemez/devredilemez), bağış şartları ve mentor yükümlülükleri burada. Jeton satışı iOS'ta açıldığında **zorunlu** hale gelir. |

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
3. Ödevini yükle — "redline" analizi al: çizimin üzerinde somut noktalar,
   neyin çalıştığı ve neyi denemen gerektiği.
4. XP kazan, seviye atla, ability chart'ının büyümesini izle.
5. Bir insan gözü istersen ödevini ücretsiz olarak bir mentora gönder.

ARTORA'YI FARKLI KILAN

• Geri bildirim her zaman yapıcı — asla kırıcı, asla cesaret kırıcı değil.
• Stil ayrımcılığı yok: manga, karikatür ya da realizm — kendi stilin içinde
  koçluk alırsın, başkasının stiline itilmezsin.
• Her gözlem uygulanabilir bir öneriyle gelir, muğlak eleştiriyle değil.
• Gelişim maceran her ödevi AI notlarıyla saklar; ne kadar yol aldığını
  gerçekten görürsün.
• Topluluk galerisinde diğer çizerlerin paylaştıklarına bak, istersen kendi
  çalışmanı paylaş.

MENTOR DESTEĞİ ÜCRETSİZ

Ödevini bir mentora göndermek jeton harcamaz. Onaylı bir mentor çizimine bakıp
kişisel geri bildirim yazar. Adil kalması için aynı mentora 24 saatte bir soru
sorabilir, aynı anda en fazla 3 açık isteğin olabilir.

JETONLAR NE İŞE YARAR

Jetonlar yapay zekâ analizleri için kullanılır. Her hafta ücretsiz jetonun
yenilenir; daha fazla analiz yapmak istersen jeton paketi alabilir ya da
Premium'a geçebilirsin. Premium daha güçlü bir AI modeli ve haftalık çok daha
yüksek bir jeton hakkı verir. Dersler, yetenek ağacı ve mentor desteği her
katmanda ücretsizdir.

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
| Unrestricted Web Access | **Hayır** — uygulamada webview/gömülü tarayıcı yok; YouTube linkleri `url_launcher` ile sistem tarayıcısına, sabit bir adrese açılıyor. Adres çubuğu veya serbest gezinme arayüzü sunulmuyor. |
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

### Yüklenecek set (2026-08-05, 2. çekim — Türkçe arayüz)

`store_assets/ios_screenshots/` altında **iki boyutta** hazır — App Store Connect
her yuva için farklı boyut istiyor, yüklediğin yuvaya göre klasörü seç:

| Yuva | Klasör | Boyut |
|---|---|---|
| 6.9" iPhone | `6.9_inch_1290x2796/` | 1290×2796 |
| 6.5" iPhone | `6.5_inch_1284x2778/` | 1284×2778 |

Yanlış klasörü yanlış yuvaya yüklersen *"The dimensions of one or more
screenshots are wrong"* hatası gelir. Tek bir yuvayı doldurmak yeterli.

Dosya adındaki numara = App Store'daki sıra. Apple arama sonuçlarında **ilk 3**
kareyi gösteriyor, sıralama ona göre yapıldı.

| # | Dosya | İçerik |
|---|---|---|
| 1 | `1_ai_redline.png` | AI Analizi: çizim + renkli işaret noktaları + "Güçlü yönlerin" |
| 2 | `2_yetenek_agaci.png` | Dersler: düğümler, kilitler, XP, "Önerilen" rozeti |
| 3 | `3_ai_gelisim_noktalari.png` | AI'ın numaralı, somut önerileri (ürünün asıl değeri) |
| 4 | `4_topluluk.png` | Topluluk galerisi |
| 5 | `5_mentorlar.png` | Mentor listesi + stil filtreleri |

**Yüklenmeyecek:**
- `ioss/…22.44.09 (2).jpeg` — mentor profili; portfolyo görselleri yüklenmiyor,
  altı tane kırık görsel ikonu görünüyor (bkz. aşağıdaki bug notu).
- `ioss/…22.27.*` — 1. çekim; arayüz İngilizce ve ekranlar boş durumda.

### Kalan bilinen eksik (kabul edildi, sonraki sürümde)

Dosyalar telefondan WhatsApp üzerinden geldiği için 946×2048'e sıkıştırılmış;
1290'a ölçeklemek yazıları bir miktar yumuşatıyor. Bir dahaki sefere
**AirDrop / iCloud / e-postada "Gerçek Boyut"** ile aktarılırsa kayıpsız
1290×2796 gelir.

### ⚠️ Ekran görüntüsünden çıkan iki gerçek sorun

1. **Mentor portfolyo görselleri yüklenmiyor.** Mentor profilinde altı kırık
   görsel ikonu, mentor listesinde de ilk kartın avatarı kırık. `imageUrl` +
   `authHeaders` ile çekilen görseller iOS'ta gelmiyor gibi görünüyor —
   inceleyen kişi de bunu görecek. Araştırılmalı.
2. **Prod veritabanında test kaydı var.** Mentor listesinde `test`, `test2` ve
   iki kez `Guest Artist` görünüyor. Gerçek kullanıcılar da bunları görüyor;
   yayın öncesi admin panelinden temizlenmeli.
