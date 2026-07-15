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
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    match settings.ai_provider:
        case "mock":
            return MockAIProvider()
        case "gemini":
            return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
        case "openrouter":
            return OpenRouterProvider(
                api_key=settings.openrouter_api_key,
                model=settings.openrouter_model,
                fallback_model=settings.openrouter_fallback_model,
            )
        case other:
            raise ValueError(
                f"Bilinmeyen AI_PROVIDER: {other!r} (geçerli: mock, gemini, openrouter)"
            )
