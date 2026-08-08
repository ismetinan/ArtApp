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
    # Premium'un aldığı model. Boşsa Premium da openrouter_model'i kullanır.
    # Ücretsiz havuz dalgalı ve rate-limit yiyor; jeton satışı açılmadan önce
    # burası GERÇEKTEN paralı bir modele ayarlanmalı (bkz. plan A4).
    openrouter_premium_model: str = ""

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
    # ESKİ MODEL: Premium'un her fatura döneminde verdiği altın jeton. Yeni
    # ekonomide Premium jeton YIĞINI değil yüksek HAFTALIK TABAN alıyor
    # (weekly_jeton_floor_premium), bu yüzden bayrak açıkken bu grant atlanır —
    # varsayılan 10 kalıyor ki bayrak kapalı davranış birebir aynı olsun.
    premium_monthly_jetons: int = 10
    # ESKİ MODEL: her 7 günde bir EKLENEN ücretsiz jeton damlası. Yeni ekonomide
    # yerini weekly_jeton_floor'a bırakıyor; jeton_ai_economy_enabled kapalıyken
    # hâlâ bu kullanılır, o yüzden silinmedi.
    weekly_free_jetons: int = 1
    # Topluluk galerisine paylaşım için gereken minimum seviye. Yeni/ciddiyetsiz
    # hesapların alakasız görsel yüklemesini engeller (müşteri isteği, 2026-08-08).
    community_share_min_level: int = 3

    # --- Jeton = AI ekonomisi (2026-08-08 kararı) -------------------------------
    # Ana bayrak. Kapalıyken davranış eski modelle BİREBİR aynı kalır (jeton =
    # mentor parası, AI = günlük kota). Açıkken: jeton = AI kullanım birimi,
    # mentorluk ücretsiz + kotalı, mentora para yalnız uygulama dışı bağışla.
    #
    # ⚠️ iOS'ta AÇMA — mobile/lib/api.dart içinde billingEnabled iOS'ta zorla
    # false, yani mağaza yok. Bayrak iOS'ta açılırsa kullanıcı haftalık taban
    # bitince jeton alamaz ve kilitlenir. iOS IAP tamamlanana kadar yalnız Android.
    jeton_ai_economy_enabled: bool = False
    # Haftalık ÜCRETSİZ jeton tabanı: bakiye bunun altındaysa buna tamamlanır,
    # üstündeyse dokunulmaz. Birikmez. Satın alınan jetonlar bundan etkilenmez.
    weekly_jeton_floor: int = 3
    weekly_jeton_floor_premium: int = 25
    # AI aksiyon fiyatları. Onboarding (seviye belirleme) ve ödev üretimi bilinçli
    # ücretsiz: ilki dönüşüm hunisinin ta kendisi, ikincisi metin + zaten önbellekli.
    ai_cost_assess_level: int = 0
    ai_cost_assignment: int = 0
    ai_cost_redline: int = 1
    ai_cost_free_analysis: int = 1
    # Modele gönderilmeden önce görselin en uzun kenarı bu piksele indirilir.
    # Görsel token'ı piksel sayısıyla ölçekleniyor ve maliyetin çoğu girdi
    # tarafında; 1024 kaliteyi düşürmeden token'ı ~2,5x azaltıyor. 0 = kapalı.
    ai_image_max_edge: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
