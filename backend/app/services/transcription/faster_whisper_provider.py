import asyncio
import math
import threading
import time
from pathlib import Path
from .base import TranscriptionProvider, TranscriptionResult, TranscriptionSegment
from app.core.config import settings

# Loading Whisper weights takes seconds and hundreds of MB; keep one model per worker process.
_MODEL_CACHE: dict[tuple[str, str, str], object] = {}
_MODEL_LOCK = threading.Lock()


def _load_model(name: str, device: str, compute_type: str):
    key = (name, device, compute_type)
    with _MODEL_LOCK:
        if key not in _MODEL_CACHE:
            from faster_whisper import WhisperModel
            _MODEL_CACHE[key] = WhisperModel(name, device=device, compute_type=compute_type)
        return _MODEL_CACHE[key]


def segment_confidence(avg_logprob: float | None, no_speech_prob: float | None) -> float | None:
    """A rough 0..1 recognition-confidence signal for flagging segments to re-check.

    exp(mean token log-probability), reduced when the model thought the audio was not speech.
    It is not the probability that the text is correct.
    """
    if avg_logprob is None:
        return None
    score = math.exp(max(avg_logprob, -10.0))
    if no_speech_prob is not None:
        score *= 1.0 - min(max(no_speech_prob, 0.0), 1.0)
    return round(min(max(score, 0.0), 1.0), 3)


class FasterWhisperProvider(TranscriptionProvider):
    name = "faster-whisper"

    def __init__(self):
        try:
            import faster_whisper
        except ImportError as exc:
            raise RuntimeError("faster-whisper is not installed. Install backend[ai].") from exc
        self.model_name = settings.whisper_model
        self.model_version = f"faster-whisper {faster_whisper.__version__} ({settings.whisper_device}/{settings.whisper_compute_type})"

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        return await asyncio.to_thread(self._transcribe_sync, audio_path)

    def _transcribe_sync(self, audio_path: Path) -> TranscriptionResult:
        model = _load_model(settings.whisper_model, settings.whisper_device, settings.whisper_compute_type)
        started = time.monotonic()
        # language=None lets Whisper detect it; multilingual=True re-detects per segment, which helps
        # with English/Urdu code-switching but does not guarantee correct script or spelling.
        segments, info = model.transcribe(
            str(audio_path), beam_size=5, vad_filter=True, multilingual=True, word_timestamps=False,
            language=settings.whisper_language or None, task="transcribe",
        )
        output = []
        texts = []
        for i, seg in enumerate(segments):
            text = seg.text.strip()
            if not text:
                continue
            texts.append(text)
            output.append(TranscriptionSegment(len(output), float(seg.start), float(seg.end), text, None,
                                               segment_confidence(getattr(seg, "avg_logprob", None), getattr(seg, "no_speech_prob", None))))
        elapsed = int(time.monotonic() - started)
        if not output:
            raise RuntimeError("No speech was recognised in the recording")
        return TranscriptionResult(" ".join(texts), getattr(info, "language", None), settings.whisper_model, self.model_version, output, elapsed)
