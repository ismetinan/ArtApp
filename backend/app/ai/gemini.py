"""Gemini adaptörü — ilk gerçek AI sağlayıcısı (ücretsiz katman).

Yapılandırılmış çıktı için Gemini'nin response_schema desteği kullanılır;
dönen JSON doğrudan Pydantic modellerimize parse edilir.
"""

from google import genai
from google.genai import types

from .base import AIProvider
from .prompts import assess_prompt, redline_prompt
from .schemas import LevelAssessment, RedlineResult


def _image_part(image: bytes) -> types.Part:
    mime = "image/png" if image[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    return types.Part.from_bytes(data=image, mime_type=mime)


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY boş — .env dosyasına anahtar ekleyin")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def _generate(self, contents: list, schema: type) -> object:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        return schema.model_validate_json(response.text)

    async def assess_level(
        self, images: list[bytes], language: str = "tr"
    ) -> LevelAssessment:
        contents = [_image_part(img) for img in images] + [assess_prompt(language)]
        return await self._generate(contents, LevelAssessment)

    async def redline_analysis(
        self, image: bytes, lesson_context: str, language: str = "tr"
    ) -> RedlineResult:
        prompt = redline_prompt(lesson_context, language)
        return await self._generate([_image_part(image), prompt], RedlineResult)
