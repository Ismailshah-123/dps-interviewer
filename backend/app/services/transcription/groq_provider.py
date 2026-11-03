import time
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.observability import ai_requests, ai_failures, ai_duration
from app.services.groq import GroqProviderError
from .base import TranscriptionProvider, TranscriptionResult, TranscriptionSegment


class GroqTranscriptionProvider(TranscriptionProvider):
    name = "groq"
    model_version = None

    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when TRANSCRIPTION_PROVIDER=groq")
        self.model_name = settings.groq_transcription_model
        self.model_version = self.model_name

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        started = time.monotonic()
        data = audio_path.read_bytes()
        if len(data) > settings.groq_max_audio_bytes:
            raise RuntimeError(
                f"Audio file exceeds Groq upload limit ({settings.groq_max_audio_bytes} bytes). "
                "Configure server-side audio chunking for larger recordings."
            )

        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
        files = {"file": (audio_path.name, data, _content_type(audio_path))}
        form = {
            "model": self.model_name,
            "response_format": "verbose_json",
            "temperature": "0",
            "timestamp_granularities[]": "segment",
        }
        started = time.monotonic()
        ai_requests.labels(self.name, "transcription", self.model_name).inc()
        try:
            async with httpx.AsyncClient(timeout=settings.groq_transcription_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.groq_base_url.rstrip('/')}/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=form,
                )
        except Exception:
            ai_failures.labels(self.name, "transcription", "transport").inc()
            raise
        finally:
            ai_duration.labels(self.name, "transcription").observe(time.monotonic() - started)
        if response.status_code >= 400:
            ai_failures.labels(self.name, "transcription", str(response.status_code)).inc()
            detail = response.text[:500]
            retry_after = response.headers.get("retry-after")
            try:
                retry_after_value = float(retry_after) if retry_after else None
            except ValueError:
                retry_after_value = None
            raise GroqProviderError(response.status_code, f"Groq transcription failed with HTTP {response.status_code}: {detail}", retry_after_value)
        body = response.json()
        segments = [
            TranscriptionSegment(
                sequence=index,
                start_seconds=float(item.get("start", 0)),
                end_seconds=float(item.get("end", 0)),
                text=str(item.get("text", "")).strip(),
                confidence=None,
            )
            for index, item in enumerate(body.get("segments") or [])
            if str(item.get("text", "")).strip()
        ]
        elapsed = int(time.monotonic() - started)
        return TranscriptionResult(
            text=str(body.get("text", "")).strip(),
            language=body.get("language"),
            model_name=self.model_name,
            model_version=self.model_version,
            segments=segments,
            processing_seconds=elapsed,
        )


def _content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".mp3": "audio/mpeg",
        ".mpeg": "audio/mpeg",
        ".mpga": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }.get(suffix, "application/octet-stream")
