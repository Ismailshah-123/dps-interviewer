import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.core.config import settings
from app.services.transcription.groq_provider import GroqTranscriptionProvider
from app.services.summarization.groq_provider import GroqSummarizationProvider


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def test_groq_transcription_parses_segments(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "groq_max_audio_bytes", 1024)
    path = tmp_path / "sample.wav"
    path.write_bytes(b"RIFF synthetic audio")

    async def fake_post(self, *args, **kwargs):
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert kwargs["data"]["model"] == "whisper-large-v3-turbo"
        return DummyResponse({
            "text": "Hello Urdu",
            "language": "ur",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello "},
                {"start": 1.5, "end": 3.0, "text": "Urdu"},
            ],
        })

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = asyncio.run(GroqTranscriptionProvider().transcribe(path))
    assert result.text == "Hello Urdu"
    assert result.language == "ur"
    assert len(result.segments) == 2
    assert result.segments[0].text == "Hello"


def test_groq_summary_validates_structured_json(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    async def fake_post(self, *args, **kwargs):
        assert kwargs["json"]["model"] == "openai/gpt-oss-20b"
        return DummyResponse({
            "choices": [{"message": {"content": json.dumps({
                "interview_overview": "Student discussed school interests.",
                "student_statements": ["Interested in science."],
            })}}]
        })

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = asyncio.run(GroqSummarizationProvider().summarize("text", []))
    assert result.interview_overview == "Student discussed school interests."
    assert result.student_statements == ["Interested in science."]


def test_groq_summary_uses_strict_json_schema(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    async def fake_post(self, *args, **kwargs):
        response_format = kwargs["json"]["response_format"]
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["strict"] is True
        schema = response_format["json_schema"]["schema"]
        assert set(schema["required"]) == set(schema["properties"])
        assert schema["additionalProperties"] is False
        return DummyResponse({
            "choices": [{"message": {"content": json.dumps({
                "interview_overview": "Student discussed school interests.",
                "parent_guardian_statements": [],
                "student_statements": ["Interested in science."],
                "educational_background": [],
                "interests_and_activities": [],
                "school_expectations": [],
                "interviewer_documented_observations": [],
                "important_topics": [],
                "follow_up_questions": [],
                "unclear_or_missing_information": [],
                "evidence": [{
                    "segment_sequence": 0,
                    "start_seconds": 0,
                    "end_seconds": 1,
                    "quote": "Interested in science.",
                }],
            })}}]
        })

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    result = asyncio.run(GroqSummarizationProvider().summarize("Interested in science.", []))
    assert result.evidence[0].quote == "Interested in science."
