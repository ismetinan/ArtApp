from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: str = "mock"  # mock | gemini | openrouter (ileride: claude, openai)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openrouter_api_key: str = ""
    # Ücretsiz model listesi dönüşümlü; güncel liste: openrouter.ai/collections/free-models
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"
    openrouter_fallback_model: str = "nvidia/nemotron-nano-12b-v2-vl:free"

    database_url: str = "postgresql+psycopg://artapp:artapp@localhost:5433/artapp"
    redis_url: str = "redis://localhost:6379/0"

    # Depolama: local (dev) | s3 (prod — Cloudflare R2, S3-uyumlu)
    storage_backend: str = "local"
    storage_dir: str = "./storage"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Google Sign-In: backend, ID token'ı bu (web/server) client ID'ye karşı doğrular
    google_client_id: str = ""

    # Beta koruması: kullanıcı başına günlük AI çağrı limiti
    ai_daily_limit: int = 10
    # Girişsiz uçlarda IP başına hız limiti (brute-force/spam koruması).
    # Testler kapatır; prod'da açık kalmalı.
    rate_limit_enabled: bool = True
    # Skora göre ders atlama eşiği: önkoşulun eksenindeki AbilityScore bu değerin
    # üstündeyse önkoşul tamamlanmadan düğüm açılır (müşteri isteği, 2026-07-19)
    skip_unlock_score: int = 60

    sentry_dsn: str = ""

    # FCM push: Firebase service account JSON'unun TAM içeriği (env'de string).
    # Boşsa push servisi sessiz no-op — dev/test Firebase'siz çalışır.
    firebase_service_account_json: str = ""

    mentor_market_enabled: bool = False  # Faz 2'de açılacak

    # Play Billing (hibrit: jeton paketleri + Premium abonelik). Kapalıyken
    # /billing uçları 404 — mentor pazarı bayrağıyla aynı desen.
    billing_enabled: bool = False
    # Play Developer API yetkili service account JSON'unun TAM içeriği (env'de
    # string). Boşken doğrulama uçları 503 döner — dev/test mock'la çalışır.
    play_service_account_json: str = ""
    android_package_name: str = "com.ismetinan.artapp"
    ai_daily_limit_premium: int = 50
    premium_monthly_jetons: int = 10
    # Faz 4: her 7 günde bir verilen ÜCRETSİZ jeton damlası (yalnız havuz mentoru
    # için harcanır). Altın satışını baltalamamak için bilinçli düşük tutulur.
    weekly_free_jetons: int = 1
    # Topluluk galerisine paylaşım için gereken minimum seviye. Yeni/ciddiyetsiz
    # hesapların alakasız görsel yüklemesini engeller (müşteri isteği, 2026-08-08).
    community_share_min_level: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
