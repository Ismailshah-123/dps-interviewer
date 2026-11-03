from pathlib import Path
from .base import TranscriptionProvider, TranscriptionResult, TranscriptionSegment
class DeterministicTranscriptionProvider(TranscriptionProvider):
    name='deterministic-test'; model_name='synthetic-fixture'; model_version='1.0'
    async def transcribe(self, audio_path: Path):
        text='Parent said the student enjoys mathematics and reading. Student said they enjoy football and science. The family expects a supportive school environment.'
        return TranscriptionResult(text=text, language='en', model_name=self.model_name, model_version=self.model_version, segments=[TranscriptionSegment(0,0,8,text)], processing_seconds=0)
