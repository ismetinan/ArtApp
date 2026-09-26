"""Aktiflik kaydı (analitik, 2026-09).

Her kimlik doğrulamalı istekte çağrılır ama DB'ye günde kullanıcı başına EN
FAZLA bir kez gider: bellek içi `_SEEN` önbelleği aynı gün tekrarlarını keser.
Süreç yeniden başlarsa önbellek boşalır — o gün ikinci bir yazma denemesi
UniqueConstraint'e takılır ve sessizce yutulur, veri bozulmaz.

Kendi commit'ini yapar: GET uçları commit etmediği için yazma, isteğin kendi
transaction'ına bırakılırsa kaybolurdu. Bağımlılık endpoint'ten ÖNCE çalıştığı
için oturumda bekleyen başka değişiklik yoktur.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.tables import User, UserActivityDay

log = logging.getLogger(__name__)

_SEEN: dict[int, str] = {}  # user_id → son yazılan gün (ISO)
_MAX_KEYS = 50_000

_PLATFORMS = {"ios", "android", "web"}


def _clean_platform(value: str | None) -> str | None:
    value = (value or "").strip().lower()
    return value if value in _PLATFORMS else None


def _clean_version(value: str | None) -> str | None:
    value = (value or "").strip()
    # Yalnız sürüm karakterleri — header'dan gelen serbest metni DB'ye yazma
    if not value or len(value) > 32 or not all(c.isalnum() or c in ".+-" for c in value):
        return None
    return value


def record(db: Session, user: User, platform: str | None, app_version: str | None) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()
    key = today.isoformat()
    if _SEEN.get(user.id) == key:
        return
    if len(_SEEN) >= _MAX_KEYS:
        _SEEN.clear()

    user.last_seen_at = now
    if (p := _clean_platform(platform)) is not None:
        user.platform = p
    if (v := _clean_version(app_version)) is not None:
        user.app_version = v
    db.add(UserActivityDay(user_id=user.id, day=today))
    try:
        db.commit()
    except IntegrityError:
        # Bugün zaten yazılmış (yeniden başlatma / eşzamanlı istek). Kullanıcı
        # alanlarını yine de kaydet.
        db.rollback()
        user.last_seen_at = now
        if (p := _clean_platform(platform)) is not None:
            user.platform = p
        if (v := _clean_version(app_version)) is not None:
            user.app_version = v
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
    except Exception:  # noqa: BLE001 — analitik hiçbir isteği düşürmemeli
        log.exception("Aktiflik kaydı başarısız (user=%s)", user.id)
        db.rollback()
        return
    _SEEN[user.id] = key
