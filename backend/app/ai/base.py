"""Sağlayıcı-bağımsız AI arayüzü.

Uygulama hiçbir yerde doğrudan Gemini/Claude/OpenAI SDK'sı çağırmaz; her şey bu
arayüz üzerinden gider. Yeni sağlayıcı = bu sınıfı uygulayan tek yeni dosya.
"""

from abc import ABC, abstractmethod

from .schemas import AssignmentBrief, LevelAssessment, ModerationVerdict, RedlineResult


class AIProvider(ABC):
    @abstractmethod
    async def assess_level(
        self, images: list[bytes], language: str = "tr"
    ) -> LevelAssessment:
        """Onboarding: 3 çizimden başlangıç seviyesi ve eksen skorları çıkarır.

        language: çıktı metinlerinin dili (tr/en) — kullanıcının dil tercihi.
        """

    @abstractmethod
    async def redline_analysis(
        self, image: bytes, lesson_context: str, language: str = "tr"
    ) -> RedlineResult:
        """Bir ödev çizimi için koordinatlı, yapıcı redline analizi üretir.

        lesson_context: ödevin bağlı olduğu dersin başlığı/konusu (ör. "temel kafa
        oranları") — model geri bildirimi derse odaklar.
        language: çıktı metinlerinin dili (tr/en).
        """

    @abstractmethod
    async def moderation_check(self, image: bytes) -> ModerationVerdict:
        """Paylaşım öncesi güvenlik kontrolü: görsel topluluğa/mentora uygun mu?

        Herkese açık yapma, mentor portfolyosu ve mentor isteği anlarında çağrılır;
        sonuç gönderi başına bir kez hesaplanıp saklanır.
        """

    @abstractmethod
    async def assignment_brief(
        self, node_title: str, node_description: str, language: str = "tr"
    ) -> AssignmentBrief:
        """Ders için somut, adım adım bir ödev görevi üretir (görsel girdisi yok).

        Uygunsa öğrenciden internetten basit bir referans obje/foto seçip onu
        farklı açılardan çizmesini ister (müşteri isteği, 2026-07-19).
        """
