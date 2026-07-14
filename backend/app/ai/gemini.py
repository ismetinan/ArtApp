"""Gemini adaptörü — ilk gerçek AI sağlayıcısı (ücretsiz katman).

Yapılandırılmış çıktı için Gemini'nin response_schema desteği kullanılır;
dönen JSON doğrudan Pydantic modellerimize parse edilir.
"""

from google import genai
from google.genai import types

from .base import AIProvider
from .schemas import LevelAssessment, RedlineResult

# Ton kuralları CLAUDE.md §5: yapıcı, somut, stil-tarafsız. Her prompt'a eklenir.
_TONE_RULES = """\
Sen kendi kendine resim öğrenen çizerlere destek olan, deneyimli ve sıcak bir mentorsun.
Kurallar:
- Ton her zaman yapıcı ve cesaretlendirici; asla aşağılayıcı, alaycı veya kırıcı değil.
- Her gözlem somut ve uygulanabilir bir öneriyle gelmeli (soyut eleştiri yok).
- Hiçbir stili (manga, karikatür, realist...) diğerinden "doğru" kabul etme;
  geri bildirimi çizerin kendi stili İÇİNDE tutarlılık üzerinden ver.
- Tüm metinleri Türkçe yaz.
"""

_REDLINE_PROMPT = _TONE_RULES + """
Bu bir öğrencinin "{lesson_context}" dersi için yüklediği ödev çizimi.
Çizimi incele ve redline (kırmızı çizgi) tarzı teknik analiz üret:
- strengths_tr: önce güçlü yönler (en az 1, en fazla 3).
- findings: en fazla 5 bulgu. Her bulgu için x ve y koordinatını, bulgunun
  görseldeki konumuna göre 0 ile 1 arasında normalize ederek ver
  (x: soldan sağa, y: yukarıdan aşağıya).
- overall_comment_tr: cesaretlendirici bir kapanış cümlesi.
Geri bildirimi mümkün olduğunca dersin konusuna odakla.
"""

_ASSESS_PROMPT = _TONE_RULES + """
Bu bir öğrencinin son 3 çizimi. Amaç: platformdaki başlangıç seviyesini belirlemek.
- Her beceri ekseni için 0-100 arası skor ver (ability_scores).
- level: 1-10 arası genel başlangıç seviyesi (1 = yeni başlayan).
- focus_axes: en zayıf 1-2 eksen (yetenek ağacında önce buraya yönlendirilecek).
- summary_tr: öğrenciye gösterilecek, güçlü yönleriyle başlayan yapıcı bir özet.
Skorlarda dürüst ama cömert ol; amaç sınıflandırmak, notlamak değil.
"""


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

    async def assess_level(self, images: list[bytes]) -> LevelAssessment:
        contents = [_image_part(img) for img in images] + [_ASSESS_PROMPT]
        return await self._generate(contents, LevelAssessment)

    async def redline_analysis(self, image: bytes, lesson_context: str) -> RedlineResult:
        prompt = _REDLINE_PROMPT.format(lesson_context=lesson_context)
        return await self._generate([_image_part(image), prompt], RedlineResult)
