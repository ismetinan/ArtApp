"""Sağlayıcı-bağımsız AI arayüzü.

Uygulama hiçbir yerde doğrudan Gemini/Claude/OpenAI SDK'sı çağırmaz; her şey bu
arayüz üzerinden gider. Yeni sağlayıcı = bu sınıfı uygulayan tek yeni dosya.
"""

from abc import ABC, abstractmethod

from .schemas import LevelAssessment, RedlineResult


class AIProvider(ABC):
    @abstractmethod
    async def assess_level(self, images: list[bytes]) -> LevelAssessment:
        """Onboarding: 3 çizimden başlangıç seviyesi ve eksen skorları çıkarır."""

    @abstractmethod
    async def redline_analysis(self, image: bytes, lesson_context: str) -> RedlineResult:
        """Bir ödev çizimi için koordinatlı, yapıcı redline analizi üretir.

        lesson_context: ödevin bağlı olduğu dersin başlığı/konusu (ör. "temel kafa
        oranları") — model geri bildirimi derse odaklar.
        """
