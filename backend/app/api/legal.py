"""Yasal sayfalar — Play Console'un istediği herkese açık gizlilik politikası URL'si.

Beta için backend'den servis edilir; ileride ayrı bir web sitesine taşınabilir.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["legal"])

_PRIVACY_HTML = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artora Gizlilik Politikası</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto;
           padding: 0 1rem; line-height: 1.6; color: #222; }
    h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 1.6rem; }
  </style>
</head>
<body>
  <h1>Artora Gizlilik Politikası</h1>
  <p><em>Son güncelleme: 8 Ağustos 2026</em></p>

  <h2>Hangi verileri topluyoruz?</h2>
  <ul>
    <li><strong>Hesap bilgileri:</strong> e-posta adresi ve görünen ad
        (Google ile girişte Google hesabınızın adı ve e-postası).</li>
    <li><strong>Çizimleriniz:</strong> seviye belirleme ve ödev analizi için
        yüklediğiniz görseller.</li>
    <li><strong>AI analiz sonuçları ve ilerleme verileri:</strong> seviye, XP,
        beceri skorları, tamamlanan dersler.</li>
  </ul>

  <h2>Verileriniz nasıl kullanılıyor?</h2>
  <p>Çizimleriniz yalnızca size geri bildirim üretmek için AI sağlayıcısına
     (OpenRouter üzerinden) iletilir; reklam veya profilleme amacıyla kullanılmaz,
     üçüncü taraflara satılmaz. Yüklediğiniz çizimler varsayılan olarak
     <strong>özeldir</strong> — siz açıkça "herkese açık" yapmadıkça yalnızca siz
     görürsünüz.</p>

  <h2>Mentor paylaşımı</h2>
  <p>Bir ödevi mentora gönderdiğinizde, o çizim ve ilgili ders bilgisi yalnızca
     size geri bildirim yazacak mentora gösterilir. Mentorlar çiziminizi başka
     amaçla kullanamaz ve platform dışında paylaşamaz.</p>

  <h2>Mentora destek (bağış)</h2>
  <p>Bir mentora destek olmayı seçerseniz, ödeme Artora üzerinden geçmez; ilgili
     bağış platformuna yönlendirilirsiniz ve ödeme bilgilerinizi Artora hiçbir
     zaman görmez veya saklamaz. Kimin bağış yaptığı bilgisi de tutulmaz.</p>

  <h2>Saklama ve silme</h2>
  <p>Verileriniz hesabınız aktif olduğu sürece saklanır. Uygulamadaki
     <strong>Profil → Hesabı Sil</strong> adımıyla hesabınızı ve tüm verilerinizi
     (çizimler dahil) kalıcı olarak silebilirsiniz. Sorular için:
     <a href="mailto:ismet17inan@gmail.com">ismet17inan@gmail.com</a></p>

  <h2>Misafir hesaplar</h2>
  <p>Misafir olarak kullandığınızda e-posta toplanmaz; verileriniz anonim bir
     hesapta tutulur ve hesabınızı kayıtlı hesaba yükselttiğinizde korunur.</p>
</body>
</html>"""


_TERMS_HTML = """<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artora Kullanım Koşulları</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto;
           padding: 0 1rem; line-height: 1.6; color: #222; }
    h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 1.6rem; }
  </style>
</head>
<body>
  <h1>Artora Kullanım Koşulları</h1>
  <p><em>Son güncelleme: 8 Ağustos 2026</em></p>

  <h2>1. Hizmet</h2>
  <p>Artora, kendi kendine çizim öğrenen kişiler için yapay zekâ destekli bir
     öğrenme platformudur. Ders videoları, yetenek ağacı ve mentor desteği
     <strong>ücretsizdir</strong>. Yapay zekâ analizleri jeton ile kullanılır;
     her hafta belirli sayıda ücretsiz jeton verilir.</p>

  <h2>2. Jeton</h2>
  <p>Jeton, yapay zekâ analizlerini kullanmaya yarayan bir uygulama içi kullanım
     birimidir. Jeton:</p>
  <ul>
    <li><strong>nakde çevrilemez</strong> ve para olarak geri ödenmez,</li>
    <li>kullanıcılar arasında <strong>devredilemez</strong> veya hediye edilemez,</li>
    <li>yalnızca Artora içinde geçerlidir, başka bir mal veya hizmet için
        kullanılamaz.</li>
  </ul>
  <p>Ücretsiz jetonlar her hafta belirlenen tabana tamamlanır ve
     <strong>biriktirilmez</strong>. Satın aldığınız jetonların
     <strong>süresi dolmaz</strong> ve haftalık yenileme bunları etkilemez.</p>

  <h2>3. Mentora destek (bağış)</h2>
  <p>Mentorluk ücretsizdir. Bir mentora destek olmak isterseniz, mentorun kendi
     bağış bağlantısına yönlendirilirsiniz. Bu bağışlarda:</p>
  <ul>
    <li>gönderdiğiniz tutarın <strong>%100'ü mentora gider</strong>; Artora
        komisyon, kesinti veya ücret almaz,</li>
    <li>bağış <strong>tamamen isteğe bağlıdır</strong>; geri bildirim almak için
        gerekli değildir,</li>
    <li>bağış uygulamada <strong>hiçbir şeyi açmaz</strong>; öncelik, rozet, daha
        hızlı cevap veya ek erişim sağlamaz.</li>
  </ul>
  <p>Ödeme Artora üzerinden geçmez. <strong>Artora bu ödemenin tarafı
     değildir</strong>, para akışına girmez ve bağıştan doğan uyuşmazlıklarda
     sorumluluk kabul etmez. İşlem, ilgili bağış platformunun kendi kural ve
     iade politikasına tabidir.</p>

  <h2>4. Mentor yükümlülükleri</h2>
  <p>Mentor olarak onaylanan kullanıcılar şunları kabul eder:</p>
  <ul>
    <li>Geri bildirim her zaman yapıcıdır; aşağılayıcı veya cesaret kırıcı dil
        kullanılmaz.</li>
    <li>Öğrenci kendi stili içinde değerlendirilir; belirli bir stile
        zorlanmaz.</li>
    <li>Geri bildirim karşılığında <strong>ödeme talep edilemez</strong>. Bağış
        yalnızca isteğe bağlı bir teşekkürdür; "önce öde, sonra bakarım" türü
        talepler yasaktır.</li>
    <li>Öğrenci çizimleri platform dışında paylaşılamaz, başka amaçla
        kullanılamaz.</li>
    <li>Metin alanlarına IBAN, kart bilgisi veya benzeri ödeme bilgisi yazılamaz;
        destek yalnızca onaylı bağış bağlantısıyla alınır.</li>
  </ul>
  <p>Bu kuralların ihlali, mentorluk yetkisinin askıya alınması veya
     kaldırılmasıyla sonuçlanır.</p>

  <h2>5. Kullanıcı içeriği ve moderasyon</h2>
  <p>Yüklediğiniz çizimlerin hakları sizde kalır. Yükleme anında otomatik bir
     yapay zekâ ön filtresi çalışır; ayrıca her paylaşım kullanıcılar tarafından
     bildirilebilir ve yönetici tarafından gizlenebilir. Başkasına ait eseri
     kendinizinmiş gibi yükleyemez, uygunsuz içerik paylaşamazsınız.</p>

  <h2>6. Satın alma ve iade</h2>
  <p>Jeton ve Premium satın alımları Google Play veya App Store üzerinden yapılır
     ve ilgili mağazanın iade politikasına tabidir. Harcanmış jetonlar iade
     edilmez.</p>

  <h2>7. Hesabınızı silme</h2>
  <p>Hesabınızı ve tüm verilerinizi uygulama içinden silebilirsiniz:
     <strong>Profil → Hesabı Sil</strong>.</p>

  <h2>8. İletişim</h2>
  <p><a href="mailto:ismet17inan@gmail.com">ismet17inan@gmail.com</a></p>
</body>
</html>"""


@router.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return _PRIVACY_HTML


@router.get("/terms", response_class=HTMLResponse)
def terms_of_service():
    return _TERMS_HTML
