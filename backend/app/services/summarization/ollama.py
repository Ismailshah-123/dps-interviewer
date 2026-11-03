import json
import httpx
from .base import SummarizationProvider
from app.core.config import settings
from app.schemas.ai import StructuredSummary

from .prompt import PROMPT_VERSION, SYSTEM_PROMPT

class OllamaProvider(SummarizationProvider):
    name = "ollama"
    model_name = settings.ollama_model
    prompt_version = f"{PROMPT_VERSION}-ollama-structured"

    async def summarize(self, transcript: str, segments: list[dict]) -> StructuredSummary:
        schema = StructuredSummary.model_json_schema()
        payload = {
            "model": settings.ollama_model,
            "stream": False,
            "format": schema,
            "system": SYSTEM_PROMPT,
            "prompt": json.dumps({"transcript": transcript, "segments": segments}, ensure_ascii=False),
            "options": {"temperature": 0},
        }
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/generate", json=payload)
            response.raise_for_status()
            body = response.json()
        raw = body.get("response")
        if not raw:
            raise RuntimeError("Ollama returned an empty response")
        return StructuredSummary.model_validate_json(raw)
