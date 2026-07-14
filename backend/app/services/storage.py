"""Dosya depolama arayüzü. Dev: yerel disk. Prod: R2/S3 (aynı arayüzle eklenecek)."""

import uuid
from pathlib import Path

from ..core.config import get_settings


def save_drawing(content: bytes, original_name: str) -> str:
    """Çizimi kaydeder, göreli yolunu döner."""
    suffix = Path(original_name).suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError(f"Desteklenmeyen dosya türü: {suffix}")
    rel_path = f"drawings/{uuid.uuid4().hex}{suffix}"
    full_path = Path(get_settings().storage_dir) / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    return rel_path


def load_drawing(rel_path: str) -> bytes:
    return (Path(get_settings().storage_dir) / rel_path).read_bytes()
