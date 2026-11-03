from pathlib import Path
from app.schemas.ai import StructuredSummary

class SummarizationProvider:
    name = "base"
    model_name = "unknown"
    prompt_version = "v1"
    async def summarize(self, transcript: str, segments: list[dict]) -> StructuredSummary:
        raise NotImplementedError
