"""Modele gönderilmeden önce görseli küçültme (Aşama 1, 2026-08-08).

Neden: sunucuda hiç küçültme yoktu — istemci ne yüklerse (maxWidth 1600, 8 MB'a
kadar) o boyutta modele gidiyordu. Görsel token'ı piksel sayısıyla ölçekleniyor
ve maliyetin ÇOĞU girdi tarafında; en uzun kenarı 1024'e indirmek görsel
token'ını kabaca 2,5× azaltıyor.

Kaliteye etkisi neden yok: model kompozisyon, oran, perspektif ve değer
geçişlerine bakıyor — piksel düzeyi detaya değil. 1024 px, bir çizimin yapısal
özelliklerini değerlendirmek için fazlasıyla yeterli.

Tasarım kuralı: bu katman ASLA akışı bozmaz. Pillow görseli açamazsa (bozuk
dosya, egzotik format) orijinal baytlar aynen geçer; analiz kalitesi düşebilir
ama istek patlamaz.
"""

import io
import logging

from PIL import Image

from ..core.config import get_settings

log = logging.getLogger(__name__)

# JPEG kalitesi: 85 gözle fark edilmeyen ama dosyayı belirgin küçülten eşik.
_JPEG_QUALITY = 85


def prepare_for_model(raw: bytes) -> bytes:
    """Görseli modele uygun boyuta indirir. Hata hâlinde orijinali döndürür."""
    max_edge = get_settings().ai_image_max_edge
    if max_edge <= 0:  # 0/negatif = küçültme kapalı (acil kaçış)
        return raw
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            # Telefon fotoğrafları EXIF ile döndürülmüş gelebiliyor; EXIF'i
            # atacağımız için önce döndürmeyi piksellere uygula, yoksa çizim
            # modele yan yatmış gider.
            from PIL import ImageOps

            im = ImageOps.exif_transpose(im)

            if im.width <= max_edge and im.height <= max_edge:
                # Zaten küçük: yine de RGB+JPEG'e çeviriyoruz — PNG çizimler
                # aynı boyutta çok daha büyük dosya oluyor ve base64 şişiyor.
                if im.format == "JPEG" and im.mode == "RGB":
                    return raw
            else:
                im.thumbnail((max_edge, max_edge), Image.LANCZOS)

            if im.mode != "RGB":
                # Alfa kanalı olan çizimler (şeffaf PNG) JPEG'e çevrilirken
                # siyah zemine düşer; beyaz zemine bastırıyoruz — kâğıt beklenen
                # arka plan ve model boş alanı "gölge" sanmasın.
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    canvas = Image.new("RGB", rgba.size, (255, 255, 255))
                    canvas.paste(rgba, mask=rgba.split()[-1])
                    im = canvas
                else:
                    im = im.convert("RGB")

            out = io.BytesIO()
            im.save(out, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
            return out.getvalue()
    except Exception:
        log.warning("Görsel küçültülemedi, orijinal gönderiliyor", exc_info=True)
        return raw
