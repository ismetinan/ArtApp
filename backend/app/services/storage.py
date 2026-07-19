"""Dosya depolama. STORAGE_BACKEND=local (dev) | s3 (prod — Cloudflare R2).

Çağıranlar yalnız save/load/delete_drawing kullanır; backend seçimi burada
gizlidir. R2, S3-uyumlu API sunduğu için boto3 ile konuşulur.
"""

import uuid
from functools import lru_cache
from pathlib import Path

from ..core.config import get_settings

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
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


def save_drawing(content: bytes, original_name: str) -> str:
    """Çizimi kaydeder, göreli yolunu döner. Tür/boyut hatasında UploadError."""
    suffix = Path(original_name).suffix.lower() or ".png"
    if suffix not in _ALLOWED_SUFFIXES:
        raise UploadError("upload_unsupported_type", suffix=suffix)
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadError("upload_too_large")
    if not _is_allowed_image(content):
        raise UploadError("upload_not_image")
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
