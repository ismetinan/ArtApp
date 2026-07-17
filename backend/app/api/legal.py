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
  <p><em>Son güncelleme: 15 Temmuz 2026 (beta sürümü)</em></p>

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


@router.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    return _PRIVACY_HTML
