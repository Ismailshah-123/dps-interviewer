import json
import time
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ConfigDict

from app.core.config import settings
from app.core.observability import ai_requests, ai_failures, ai_duration
from app.services.groq import GroqProviderError

FIELD_IDS = [
    "q1a_ideal_school", "q1b_other_schools", "q2a_daily_routine", "q2b_milestones_independence",
    "q2c_sharing_caring", "q2d_endearing_quality", "q3_medical_information", "q4a_financial_flexibility",
    "q4b_camps_programs", "q4c_family_vacations", "q4d_family_professions", "q5a_social_media_use",
    "q5b_school_opinions", "q6a_school_policies", "q6b_policy_disagreement", "q6c_stress_situations",
    "q7a_child_technology", "q7b_tablets_books", "q8_personal_opinion",
]

FieldId = Literal[
    "q1a_ideal_school", "q1b_other_schools", "q2a_daily_routine", "q2b_milestones_independence",
    "q2c_sharing_caring", "q2d_endearing_quality", "q3_medical_information", "q4a_financial_flexibility",
    "q4b_camps_programs", "q4c_family_vacations", "q4d_family_professions", "q5a_social_media_use",
    "q5b_school_opinions", "q6a_school_policies", "q6b_policy_disagreement", "q6c_stress_situations",
    "q7a_child_technology", "q7b_tablets_books", "q8_personal_opinion",
]

class FormAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_id: FieldId
    text: str = Field(default="", max_length=20000)
    evidence_quotes: list[str] = Field(default_factory=list, max_length=5)

class DPSFormExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[FormAnswer] = Field(default_factory=list, max_length=19)


def _schema() -> dict:
    schema = DPSFormExtraction.model_json_schema()

    def enforce_strict_schema(node):
        if isinstance(node, dict):
            properties = node.get("properties")

            if isinstance(properties, dict):
                # Groq strict mode requires every property to be required
                node["required"] = list(properties.keys())
                node["additionalProperties"] = False

            for value in node.values():
                enforce_strict_schema(value)

        elif isinstance(node, list):
            for item in node:
                enforce_strict_schema(item)

    enforce_strict_schema(schema)
    return schema

SYSTEM_PROMPT = """You are the form-extraction assistant for Dawood Public School's Parent's Interview Form Pre-Primary 2026-27.

The input is an interview transcript that may contain English, Urdu, or mixed English and Urdu.
Your job is to fill the supplied digital form fields using ONLY information explicitly stated in the transcript.

Rules:
1. Never invent, infer, guess, or fill an answer merely because the question was asked.
2. If a question was not answered or the answer is unclear, return an empty text for that field.
3. Preserve the parent's actual meaning. You may translate Urdu into concise professional English for the form, but do not change facts.
4. Preserve names, dates, numbers, grades, medical terms, and other exact values carefully. Do not normalize uncertain values.
5. For fields that ask for both Father's Perspective and Mother's Perspective, clearly label the two perspectives only when the transcript identifies them. Example: "Father: ...\nMother: ...". If only one is identified, label only that perspective.
6. q6c_stress_situations must preserve Home, Work, and Parenting distinctions when discussed.
7. q3_medical_information may contain health or special-needs information only when the parent explicitly stated it. Never infer a medical condition.
8. q4d_family_professions should only contain professions or education/career information explicitly discussed.
9. q8_personal_opinion should capture the parent's actual admission-process feedback, questions, or comments.
10. Do not include interviewer observations unless they were explicitly stated by the interviewer in the transcript; this model does not fill the manual interviewer-observations field.
11. evidence_quotes should contain short exact transcript excerpts supporting the answer. Do not invent quotations.
12. Return only fields that have an explicit answer. Empty fields may be omitted from answers.
"""

class DPSFormExtractor:
    name = "groq-form"

    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when FORM_EXTRACTION_PROVIDER=groq")
        self.model_name = settings.groq_form_model

    async def extract(self, transcript: str, summary: dict) -> DPSFormExtraction:
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({"transcript": transcript, "summary": summary, "field_ids": FIELD_IDS}, ensure_ascii=False)},
            ],
            "model": self.model_name,
            "temperature": 0,
            "reasoning_effort": "low",
            "max_completion_tokens": settings.groq_form_max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "dps_parent_interview_form", "strict": True, "schema": _schema()},
            },
        }
        headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
        started = time.monotonic()
        ai_requests.labels(self.name, "form_extraction", self.model_name).inc()
        try:
            async with httpx.AsyncClient(timeout=settings.groq_form_timeout_seconds) as client:
                response = await client.post(f"{settings.groq_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
        except Exception:
            ai_failures.labels(self.name, "form_extraction", "transport").inc()
            raise
        finally:
            ai_duration.labels(self.name, "form_extraction").observe(time.monotonic() - started)
        if response.status_code >= 400:
            ai_failures.labels(self.name, "form_extraction", str(response.status_code)).inc()
            retry_after = response.headers.get("retry-after")
            try:
                retry_after_value = float(retry_after) if retry_after else None
            except ValueError:
                retry_after_value = None
            raise GroqProviderError(response.status_code, f"Groq form extraction failed with HTTP {response.status_code}: {response.text[:500]}", retry_after_value)
        choices = response.json().get("choices") or []
        raw = choices[0].get("message", {}).get("content") if choices else None
        if not raw:
            ai_failures.labels(self.name, "form_extraction", "empty_response").inc()
            raise RuntimeError("Groq returned an empty DPS form response")
        try:
            return DPSFormExtraction.model_validate_json(raw)
        except Exception as exc:
            ai_failures.labels(self.name, "form_extraction", "schema_validation").inc()
            raise RuntimeError("Groq returned JSON that does not match the DPS form schema") from exc
