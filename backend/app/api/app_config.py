"""İstemci yapılandırması: güncelleme uyarısı (2026-09).

Girişsiz uç — uygulama oturum açılmadan önce de sorabilsin. Karar istemcide
verilir (kendi sürüm adını bilen o); sunucu yalnız eşikleri ve mağaza
bağlantısını söyler. Böylece eşikler Railway'den değiştirilir, yeni sürüm
gerekmez.
"""

from fastapi import APIRouter, Query

from ..core.config import get_settings

router = APIRouter(tags=["app"])


@router.get("/app-config")
def app_config(platform: str = Query(default="android", max_length=10)):
    s = get_settings()
    ios = platform.lower() == "ios"
    return {
        "latest_version": (s.app_latest_version_ios if ios else s.app_latest_version_android)
        or None,
        "min_version": (s.app_min_version_ios if ios else s.app_min_version_android) or None,
        "store_url": s.app_store_url_ios
        if ios
        else f"https://play.google.com/store/apps/details?id={s.android_package_name}",
    }
