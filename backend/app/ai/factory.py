"""AI_PROVIDER env değişkenine göre sağlayıcı seçimi.

Yeni sağlayıcı eklemek: adaptör dosyasını yaz, buradaki sözlüğe bir satır ekle.
"""

from functools import lru_cache

from ..core.config import get_settings
from .base import AIProvider
from .gemini import GeminiProvider
from .mock import MockAIProvider
from .openrouter import OpenRouterProvider


@lru_cache
def get_ai_provider(premium: bool = False) -> AIProvider:
    """Aktif sağlayıcıyı döndürür.

    premium=True: Premium abonenin aldığı güçlü model (OPENROUTER_PREMIUM_MODEL).
    Ayar boşsa sessizce normal modele düşer — Premium yine çalışır, sadece
    farkı olmaz. Bu bilinçli: yanlış yapılandırma yüzünden ödeme yapan
    kullanıcının analizi hiç çalışmamasındansa normal modelle çalışsın.

    lru_cache parametreye göre iki ayrı örnek tutar (normal + premium).
    """
    settings = get_settings()
    match settings.ai_provider:
        case "mock":
            return MockAIProvider()
        case "gemini":
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        case "openrouter":
            model = settings.openrouter_model
            if premium and settings.openrouter_premium_model:
                model = settings.openrouter_premium_model
            return OpenRouterProvider(
                api_key=settings.openrouter_api_key,
                model=model,
                fallback_model=settings.openrouter_fallback_model,
            )
        case other:
            raise ValueError(
                f"Bilinmeyen AI_PROVIDER: {other!r} (geçerli: mock, gemini, openrouter)"
            )
