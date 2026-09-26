"""Dosya depolama. STORAGE_BACKEND=local (dev) | s3 (prod — Cloudflare R2).

Çağıranlar yalnız save/load/delete_drawing kullanır; backend seçimi burada
gizlidir. R2, S3-uyumlu API sunduğu için boto3 ile konuşulur.
"""

import io
import logging
import uuid
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

from ..core.config import get_settings

log = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
# Sıkıştırma bombası koruması: küçük dosya, devasa piksel sayısı (8 MB PNG
# 50k×50k açılabilir → RAM tükenir). ~40 MP her telefon kamerasını karşılar.
MAX_IMAGE_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
# im.info içinde kimlik/konum taşıyabilecek meta anahtarları
_META_KEYS = ("exif", "xmp", "XML:com.adobe.xmp", "comment", "Comment", "Description")
_ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class UploadError(ValueError):
    """Tür/boyut hatası. `code` messages.py kataloğundaki anahtardır — endpoint
    kullanıcının diline çevirir (bu katman dil bilmez)."""

    def __init__(self, code: str, **params: object):
        super().__init__(code)
        self.code = code
        self.params = params


@lru_cache
def _s3_client():
    import boto3  # lazy: local modda boto3 gerekmez

    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        region_name="auto",
    )


def _is_allowed_image(content: bytes) -> bool:
    """İçeriğin gerçekten PNG/JPEG/WebP olduğunu magic byte'larla doğrular —
    uzantısı .png yapılmış rastgele dosya (HTML, script...) depoya giremez."""
    return (
        content.startswith(b"\x89PNG\r\n\x1a\n")
        or content.startswith(b"\xff\xd8\xff")
        or (content[:4] == b"RIFF" and content[8:12] == b"WEBP")
    )


async def read_upload(file) -> bytes:
    """UploadFile içeriğini boyut sınırıyla okur — sınırsız read() ile devasa
    gövdenin RAM'e alınmasını (bellek DoS) engeller."""
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadError("upload_too_large")
    return content


def strip_metadata(content: bytes) -> bytes:
    """EXIF/XMP/yorum meta verisini atar (GPS konumu, cihaz modeli, çekim
    zamanı). Telefonla çekilen çizim fotoğrafları GPS taşıyabiliyor ve
    topluluk galerisinde dosya olduğu gibi sunuluyor — kullanıcının (reşit
    olmayanlar dahil) ev konumu sızabilirdi.

    Meta yoksa baytlar AYNEN döner (gereksiz yeniden sıkıştırma yok).
    EXIF döndürmesi piksellere uygulanır ki çizim yan yatmasın. Açılamayan ya
    da piksel sınırını aşan görsel UploadError ile reddedilir."""
    try:
        # verify() açılıştan hemen sonra çağrılmalı ve görüntüyü kullanılamaz
        # bırakıyor → doğrulama ve işleme için iki ayrı açılış.
        with Image.open(io.BytesIO(content)) as probe:
            # Pillow sınırın 1-2 katı arasında yalnız UYARI veriyor; açık kontrol
            if probe.width * probe.height > MAX_IMAGE_PIXELS:
                raise UploadError("upload_too_large")
            probe.verify()  # bozuk/sahte dosyayı yakala
        with Image.open(io.BytesIO(content)) as im:
            fmt = im.format
            has_meta = bool(im.getexif()) or any(k in im.info for k in _META_KEYS)
            if not has_meta:
                return content
            im.load()
            icc = im.info.get("icc_profile")
            clean = ImageOps.exif_transpose(im)
            out = io.BytesIO()
            kwargs: dict = {"icc_profile": icc} if icc else {}
            if fmt == "JPEG":
                if clean.mode not in ("RGB", "L", "CMYK"):
                    clean = clean.convert("RGB")
                clean.save(out, "JPEG", quality=92, optimize=True, **kwargs)
            elif fmt == "WEBP":
                clean.save(out, "WEBP", quality=92, **kwargs)
            else:
                clean.save(out, "PNG", optimize=True, **kwargs)
            return out.getvalue()
    except Image.DecompressionBombError:
        raise UploadError("upload_too_large")
    except UploadError:
        raise
    except Exception:  # noqa: BLE001 — Pillow'un açamadığı "görsel" depoya girmez
        log.info("Görsel açılamadı, reddedildi")
        raise UploadError("upload_not_image")


def save_drawing(content: bytes, original_name: str) -> str:
    """Çizimi kaydeder, göreli yolunu döner. Tür/boyut hatasında UploadError."""
    suffix = Path(original_name).suffix.lower() or ".png"
    if suffix not in _ALLOWED_SUFFIXES:
        raise UploadError("upload_unsupported_type", suffix=suffix)
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadError("upload_too_large")
    if not _is_allowed_image(content):
        raise UploadError("upload_not_image")
    content = strip_metadata(content)
    rel_path = f"drawings/{uuid.uuid4().hex}{suffix}"

    settings = get_settings()
    if settings.storage_backend == "s3":
        _s3_client().put_object(Bucket=settings.s3_bucket, Key=rel_path, Body=content)
    else:
        full_path = Path(settings.storage_dir) / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
    return rel_path


def load_drawing(rel_path: str) -> bytes:
    """Kaydı okur; yoksa FileNotFoundError."""
    settings = get_settings()
    if settings.storage_backend == "s3":
        try:
            obj = _s3_client().get_object(Bucket=settings.s3_bucket, Key=rel_path)
        except _s3_client().exceptions.NoSuchKey:
            raise FileNotFoundError(rel_path)
        return obj["Body"].read()
    return (Path(settings.storage_dir) / rel_path).read_bytes()


def delete_drawing(rel_path: str) -> None:
    settings = get_settings()
    if settings.storage_backend == "s3":
        _s3_client().delete_object(Bucket=settings.s3_bucket, Key=rel_path)
    else:
        (Path(settings.storage_dir) / rel_path).unlink(missing_ok=True)
