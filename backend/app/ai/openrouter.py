"""OpenRouter adaptörü — OpenAI-uyumlu chat/completions API'si.

Tek anahtarla düzinelerce modele (Qwen2.5-VL, Gemma vb. ücretsiz vision
modelleri dahil) erişim sağlar; model .env'deki OPENROUTER_MODEL ile seçilir.
Aynı kod şekli, base_url değişince Groq/Mistral gibi diğer OpenAI-uyumlu
uçlara da uyar.
"""

import base64
import json

import httpx
from pydantic import BaseModel

from .base import AIProvider
from .prompts import assess_prompt, redline_prompt
from .schemas import LevelAssessment, RedlineResult

_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _image_part(image: bytes) -> dict:
    mime = "image/png" if image[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    data_url = f"data:{mime};base64,{base64.b64encode(image).decode()}"
    return {"type": "image_url", "image_url": {"url": data_url}}


def _strip_fences(text: str) -> str:
    """Bazı ücretsiz modeller JSON'u ```json ... ``` bloğuna sarar."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


# Ücretsiz model havuzları dalgalı: bu durumlarda yeniden dene / yedek modele geç
_RETRYABLE_STATUS = {404, 408, 429, 500, 502, 503, 504}


class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str, model: str, fallback_model: str = ""):
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY boş — .env dosyasına anahtar ekleyin")
        self._api_key = api_key
        self._model = model
        self._fallback_model = fallback_model

    async def _generate[T: BaseModel](self, content: list[dict], schema: type[T]) -> T:
        # Sıra: asıl model, asıl model (retry), yedek model
        attempts = [self._model, self._model]
        if self._fallback_model and self._fallback_model != self._model:
            attempts.append(self._fallback_model)
        last_error: Exception | None = None
        for model in attempts:
            try:
                return await self._generate_once(content, schema, model)
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in _RETRYABLE_STATUS:
                    raise
                last_error = e
            except (RuntimeError, ValueError) as e:  # hata gövdesi / bozuk JSON
                last_error = e
        raise last_error

    async def _generate_once[T: BaseModel](
        self, content: list[dict], schema: type[T], model: str
    ) -> T:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema.model_json_schema(),
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            # OpenRouter sıralama/istatistik başlıkları (opsiyonel ama önerilen)
            "HTTP-Referer": "https://github.com/artapp",
            "X-Title": "Artora",
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()
        if "choices" not in body:  # OpenRouter bazen 200 gövdesinde hata döner
            raise RuntimeError(f"OpenRouter hata döndürdü: {json.dumps(body)[:500]}")
        text = body["choices"][0]["message"]["content"]
        return schema.model_validate_json(_strip_fences(text))

    async def assess_level(
        self, images: list[bytes], language: str = "tr"
    ) -> LevelAssessment:
        content = [_image_part(img) for img in images]
        content.append({"type": "text", "text": assess_prompt(language)})
        return await self._generate(content, LevelAssessment)

    async def redline_analysis(
        self, image: bytes, lesson_context: str, language: str = "tr"
    ) -> RedlineResult:
        content = [
            _image_part(image),
            {"type": "text", "text": redline_prompt(lesson_context, language)},
        ]
        return await self._generate(content, RedlineResult)
