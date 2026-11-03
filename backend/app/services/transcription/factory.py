from .base import TranscriptionProvider
from .faster_whisper_provider import FasterWhisperProvider
from .deterministic import DeterministicTranscriptionProvider
from .groq_provider import GroqTranscriptionProvider

class UnavailableTranscriptionProvider(TranscriptionProvider):
    name = "unavailable"
    async def transcribe(self, audio_path):
        raise RuntimeError("No transcription provider is configured. Set TRANSCRIPTION_PROVIDER=faster-whisper and install backend[ai].")

def get_transcription_provider() -> TranscriptionProvider:
    from app.core.config import settings
    if settings.transcription_provider == "deterministic-test": return DeterministicTranscriptionProvider()
    if settings.transcription_provider == "faster-whisper":
        return FasterWhisperProvider()
    if settings.transcription_provider == "groq":
        return GroqTranscriptionProvider()
    return UnavailableTranscriptionProvider()
