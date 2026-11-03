from dataclasses import dataclass
from pathlib import Path

@dataclass
class TranscriptionSegment:
    sequence: int
    start_seconds: float
    end_seconds: float
    text: str
    speaker_label: str | None = None
    confidence: float | None = None

@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    model_name: str
    model_version: str | None
    segments: list[TranscriptionSegment]
    processing_seconds: int | None

class TranscriptionProvider:
    name = "base"
    model_name = "unknown"
    model_version = None
    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise NotImplementedError
