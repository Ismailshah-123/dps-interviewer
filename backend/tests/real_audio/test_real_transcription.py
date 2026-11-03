"""Opt-in: real Whisper inference on synthetic audio. Downloads model weights on first run.

Run with:  DPS_REAL_AUDIO=1 WHISPER_MODEL=small WHISPER_DEVICE=cpu pytest tests/real_audio -s
Never part of the default suite.
"""
import asyncio
import os
import time
from pathlib import Path

import re

import pytest

SAMPLE = Path(__file__).resolve().parents[3] / "samples" / "synthetic" / "english_interview.webm"
pytestmark = pytest.mark.skipif(os.environ.get("DPS_REAL_AUDIO") != "1", reason="set DPS_REAL_AUDIO=1 to run real model inference")


def test_faster_whisper_transcribes_synthetic_english():
    from app.core.config import settings
    from app.services.transcription.faster_whisper_provider import FasterWhisperProvider

    for key in ("whisper_model", "whisper_device", "whisper_compute_type"):
        if os.environ.get(key.upper()):
            setattr(settings, key, os.environ[key.upper()])
    assert SAMPLE.exists(), "run scripts/make_synthetic_interview.ps1 first"
    provider = FasterWhisperProvider()
    started = time.monotonic()
    result = asyncio.run(provider.transcribe(SAMPLE))
    wall = time.monotonic() - started
    text = result.text.lower()
    print(f"\nmodel={result.model_name} version={result.model_version} language={result.language} "
          f"segments={len(result.segments)} wall_seconds={wall:.1f}")
    for s in result.segments:
        print(f"  [{s.start_seconds:6.1f}-{s.end_seconds:6.1f}] conf={s.confidence} {s.text}")
    assert result.language == "en"
    assert result.segments and all(s.end_seconds >= s.start_seconds for s in result.segments)
    # Content checks: key facts and the negation must survive transcription.
    # Whisper may write numbers as digits, so accept either form.
    for pattern in (r"class (three|3)", r"green valley", r"piano", r"(do not|don't) like painting", r"(fourteenth|14)"):
        assert re.search(pattern, text), pattern
