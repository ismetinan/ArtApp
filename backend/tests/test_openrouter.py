"""OpenRouter adaptörü birim testleri — httpx sahte yanıtlarla, ağ erişimi yok."""

import asyncio
import json

import httpx
import pytest

from app.ai.openrouter import OpenRouterProvider, _strip_fences

_REDLINE_JSON = json.dumps(
    {
        "strengths_tr": ["Çizgi akıcılığı güzel."],
        "findings": [
            {
                "skill_axis": "oran",
                "x": 0.4,
                "y": 0.3,
                "severity": "orta",
                "message_tr": "Baş gövdeye göre büyük.",
                "suggestion_tr": "Baş boyu ölçüsüyle kontrol et.",
            }
        ],
        "overall_comment_tr": "Devam et!",
    }
)


class _FakeResponse:
    def __init__(self, body: dict, status_code: int = 200):
        self._body = body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test")
            raise httpx.HTTPStatusError(
                "hata",
                request=request,
                response=httpx.Response(self.status_code, request=request),
            )

    def json(self):
        return self._body


class _FakeClient:
    """httpx.AsyncClient yerine geçer; sıradaki yanıtı döndürür."""

    next_response: _FakeResponse = None
    last_payload: dict = None

    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        _FakeClient.last_payload = json
        return _FakeClient.next_response


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr("app.ai.openrouter.httpx.AsyncClient", _FakeClient)
    return OpenRouterProvider(api_key="test-key", model="test/model:free")


def _chat_body(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def test_redline_happy_path(provider):
    _FakeClient.next_response = _FakeResponse(_chat_body(_REDLINE_JSON))
    result = asyncio.run(provider.redline_analysis(b"fakeimg", "Temel Oranlar"))
    assert result.findings[0].skill_axis == "oran"
    assert result.strengths_tr
    # json_schema yapılandırılmış çıktı istenmiş olmalı
    assert _FakeClient.last_payload["response_format"]["type"] == "json_schema"


def test_fenced_json_fallback(provider):
    fenced = f"```json\n{_REDLINE_JSON}\n```"
    _FakeClient.next_response = _FakeResponse(_chat_body(fenced))
    result = asyncio.run(provider.redline_analysis(b"fakeimg", "Temel Oranlar"))
    assert result.overall_comment_tr == "Devam et!"


def test_http_error_raises(provider):
    _FakeClient.next_response = _FakeResponse({}, status_code=429)
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(provider.redline_analysis(b"fakeimg", "Temel Oranlar"))


def test_error_body_without_choices_raises(provider):
    _FakeClient.next_response = _FakeResponse({"error": {"message": "No endpoints found"}})
    with pytest.raises(RuntimeError, match="OpenRouter"):
        asyncio.run(provider.redline_analysis(b"fakeimg", "Temel Oranlar"))


def test_missing_key_rejected():
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider(api_key="", model="test/model:free")


def test_strip_fences_variants():
    assert _strip_fences('{"a": 1}') == '{"a": 1}'
    assert _strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_fences('```\n{"a": 1}\n```') == '{"a": 1}'
