import asyncio
from pathlib import Path
from app.services.transcription.deterministic import DeterministicTranscriptionProvider
from app.services.summarization.deterministic import DeterministicSummarizationProvider

def test_deterministic_transcription():
    result=asyncio.run(DeterministicTranscriptionProvider().transcribe(Path('fixture.wav')))
    assert result.segments and result.language=='en'

def test_deterministic_summary():
    result=asyncio.run(DeterministicSummarizationProvider().summarize('text', []))
    assert result.interview_overview
    assert result.student_statements
