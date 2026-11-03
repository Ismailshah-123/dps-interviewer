"""Run a real Groq demo smoke test with an audio file and optional transcript summary.

Usage:
  GROQ_API_KEY=... python scripts/groq_demo_smoke.py ./interview.wav

The script makes real provider calls and should only be used with consented demo data.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY is not set", file=sys.stderr)
        return 2
    if not args.audio.is_file():
        print(f"ERROR: audio file not found: {args.audio}", file=sys.stderr)
        return 2

    from app.core.config import settings
    from app.services.transcription.groq_provider import GroqTranscriptionProvider
    from app.services.summarization.groq_provider import GroqSummarizationProvider

    settings.groq_api_key = os.environ["GROQ_API_KEY"]
    settings.transcription_provider = "groq"
    settings.summarization_provider = "groq"

    print(f"Transcription model: {settings.groq_transcription_model}")
    transcription = await GroqTranscriptionProvider().transcribe(args.audio)
    print(f"Language: {transcription.language or 'unknown'}")
    print(f"Segments: {len(transcription.segments)}")
    print(f"Transcript characters: {len(transcription.text)}")

    segments = [
        {
            "sequence": item.sequence,
            "start_seconds": item.start_seconds,
            "end_seconds": item.end_seconds,
            "text": item.text,
        }
        for item in transcription.segments
    ]
    summary = await GroqSummarizationProvider().summarize(transcription.text, segments)
    print(f"Summary model: {settings.groq_summary_model}")
    print("Structured summary validation: PASS")
    print(f"Evidence items: {len(summary.evidence)}")
    print(f"Unclear/missing items: {len(summary.unclear_or_missing_information)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
