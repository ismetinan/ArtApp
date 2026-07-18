# Faz 0 Doğrulama Raporu — AI Redline Stil Tarafsızlığı

**Tarih:** 2026-07-18 · **Sağlayıcı:** OpenRouter (prod ile aynı adaptör + prompt'lar)
· **Örneklem:** 8 gerçek çizim — 3 manga, 3 karikatür, 2 realist (karakalem)
· **Koşum:** `prototype/redline_test.py`, overlay çıktıları `prototype/output/`

## Sonuç: GEÇTİ ✅

CLAUDE.md Faz 0 kapısındaki soru — *"bulgular stiller arasında tutarlı ve
stil-tarafsız mı?"* — üç stilde de olumlu cevaplandı.

### Kanıtlar

1. **Önyargı işareti yok.** Hiçbir manga/karikatür çizimine "gerçekçi değil"
   tarzı geri bildirim verilmedi. Tersine, model stili açıkça tanıyıp içinde
   kaldı: karikatürde *"abartılı anlatım (karikatürize tarz) çok tutarlı...
   anatomik bozulmaların stilin bir parçası olduğunu unutma"*, mangada
   *"tarzınla uyumlu"*, *"stilistik olarak tutarlı"* ifadeleri kullanıldı.
   Öneriler stilin KENDİ içinde tutarlılığı hedefliyor (CLAUDE.md §5 kuralı).

2. **Stiller arası tutarlılık.** Her stil 3-4 bulgu aldı, benzer şiddet
   dağılımıyla (dusuk/orta); güçlü yönler her analizde en az 2 madde.
   Bir stile sistematik olarak daha sert/yumuşak davranma gözlenmedi.

3. **Somut ve uygulanabilir öneriler.** Soyut eleştiri yok; her bulguda
   egzersiz/teknik önerisi var: foreshortening eskizi, eli kutu formundan
   inşa etme, çizgi kalınlığı (line weight) varyasyonu, şapkayı küre üzerine
   oturtma, baş boyu ölçüsü vb.

4. **Ton.** Tüm kapanışlar cesaretlendirici; kırıcı ifade yok (ton koruması
   devreye girmek zorunda kalmadı).

5. **Koordinatlar.** Overlay işaretleri bölge düzeyinde isabetli (ağız, göz,
   şapka, gövde gibi bahsedilen bölgelere düşüyor); piksel hassasiyeti yok ama
   Faz 1'in "bölgeye işaret et" amacı için yeterli.

### Gözlenen zayıflıklar (blokaj değil, iyileştirme adayı)

- **Şiddet dağılımı cömert:** hiç `yuksek` bulgu çıkmadı — hedef kitle
  (kırılgan motivasyon) için bilinçli tasarım, ama ileri seviye kullanıcıda
  geri bildirimi sulandırabilir.
- **Övgü/bulgu karışımı:** model bazen güçlü yönü "bulgu" olarak listeliyor
  (ör. "yüz hatları başarılı" + dusuk şiddet). Prompt'a "findings yalnız
  gelişim alanları içersin" netliği eklenebilir.
- Tek koşumluk örneklem küçük (8 görsel); beta telemetrisiyle izlemeye devam.

### Karar

Faz 0 "git" dedi — mevcut mimari (metin+koordinat tabanlı VLM yaklaşımı,
sağlayıcı-bağımsız katman) değişiklik gerektirmiyor. Hibrit yaklaşım
(MediaPipe/OpenPose) Faz 2+ değerlendirmesi olarak kalır.
