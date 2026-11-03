import asyncio
import json

import httpx
import pytest

from app.core.config import settings
from app.services.groq import GroqProviderError
from app.services.transcription.groq_provider import GroqTranscriptionProvider
from app.services.summarization.groq_provider import GroqSummarizationProvider


class DummyResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_demo_summary_model_is_lightweight_default():
    assert settings.groq_summary_model == "openai/gpt-oss-20b"


def test_groq_429_exposes_retry_after(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    path = tmp_path / "sample.wav"
    path.write_bytes(b"RIFF synthetic audio")

    async def fake_post(self, *args, **kwargs):
        return DummyResponse({"error": {"message": "rate limited"}}, 429, {"retry-after": "12"})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(GroqProviderError) as exc:
        asyncio.run(GroqTranscriptionProvider().transcribe(path))
    assert exc.value.status_code == 429
    assert exc.value.retryable is True
    assert exc.value.retry_after_seconds == 12


def test_groq_server_error_is_retryable(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    async def fake_post(self, *args, **kwargs):
        return DummyResponse({"error": {"message": "temporary"}}, 503)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(GroqProviderError) as exc:
        asyncio.run(GroqSummarizationProvider().summarize("text", []))
    assert exc.value.retryable is True


def test_groq_auth_error_is_not_retryable(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    async def fake_post(self, *args, **kwargs):
        return DummyResponse({"error": {"message": "unauthorized"}}, 401)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    with pytest.raises(GroqProviderError) as exc:
        asyncio.run(GroqSummarizationProvider().summarize("text", []))
    assert exc.value.retryable is False


def test_free_demo_audio_guard_is_25_mib():
    assert settings.groq_max_audio_bytes == 26_214_400
