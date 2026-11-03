import json
import time

import httpx

from app.core.config import settings
from app.core.observability import ai_requests, ai_failures, ai_duration
from app.services.groq import GroqProviderError
from app.schemas.ai import StructuredSummary
from .base import SummarizationProvider
from .prompt import PROMPT_VERSION, SYSTEM_PROMPT





def _strict_schema() -> dict:
    schema = StructuredSummary.model_json_schema()
    schema["additionalProperties"] = False
    schema["required"] = list(schema.get("properties", {}).keys())
    evidence = schema.get("$defs", {}).get("Evidence")
    if evidence:
        evidence["additionalProperties"] = False
        evidence["required"] = list(evidence.get("properties", {}).keys())
    return schema


class GroqSummarizationProvider(SummarizationProvider):
    name = "groq"
    prompt_version = f"{PROMPT_VERSION}-groq-structured"

    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when SUMMARIZATION_PROVIDER=groq")
        self.model_name = settings.groq_summary_model

    async def summarize(self, transcript: str, segments: list[dict]) -> StructuredSummary:
        schema = _strict_schema()
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"output_schema": schema, "transcript": transcript, "segments": segments},
                        ensure_ascii=False,
                    ),
                },
            ],
            "model": self.model_name,
            "temperature": 0,
            "reasoning_effort": "low",
            "max_completion_tokens": settings.groq_summary_max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "dps_interview_summary",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        started = time.monotonic()
        ai_requests.labels(self.name, "summarization", self.model_name).inc()
        try:
            async with httpx.AsyncClient(timeout=settings.groq_summary_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.groq_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except Exception:
            ai_failures.labels(self.name, "summarization", "transport").inc()
            raise
        finally:
            ai_duration.labels(self.name, "summarization").observe(time.monotonic() - started)
        if response.status_code >= 400:
            ai_failures.labels(self.name, "summarization", str(response.status_code)).inc()
            detail = response.text[:500]
            retry_after = response.headers.get("retry-after")
            try:
                retry_after_value = float(retry_after) if retry_after else None
            except ValueError:
                retry_after_value = None
            raise GroqProviderError(response.status_code, f"Groq summarization failed with HTTP {response.status_code}: {detail}", retry_after_value)
        body = response.json()
        choices = body.get("choices") or []
        if not choices or not choices[0].get("message", {}).get("content"):
            ai_failures.labels(self.name, "summarization", "empty_response").inc()
            raise RuntimeError("Groq returned an empty summary response")
        raw = choices[0]["message"]["content"]
        try:
            return StructuredSummary.model_validate_json(raw)
        except Exception as exc:
            ai_failures.labels(self.name, "summarization", "schema_validation").inc()
            raise RuntimeError("Groq returned JSON that does not match the summary schema") from exc
