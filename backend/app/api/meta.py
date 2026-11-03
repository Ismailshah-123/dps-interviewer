from fastapi import APIRouter

from app.core.config import settings
from app.models.models import InterviewStatus, Role

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("")
async def meta() -> dict:
    """Return non-secret frontend integration metadata.

    This endpoint intentionally exposes configuration needed by the frontend while
    excluding credentials, database URLs, storage paths, and other secrets.
    """
    return {
        "application": settings.app_name,
        "api_version": "0.18.0",
        "environment": settings.environment,
        "roles": [role.value for role in Role],
        "interview_statuses": [status.value for status in InterviewStatus],
        "features": {
            "audio_recording": True,
            "ai_transcription": settings.transcription_provider != "unavailable",
            "ai_summarization": settings.summarization_provider != "unavailable",
            "pdf_export": True,
            "review_workflow": True,
            "metrics": settings.metrics_enabled,
        },
        # Providers that send interview content off this machine. The UI shows a warning when non-empty.
        "external_ai": sorted({p for p in (settings.transcription_provider, settings.summarization_provider) if p == "groq"}),
        "upload": {
            "max_bytes": settings.max_upload_bytes,
            "allowed_mime_types": settings.allowed_audio_mime_types,
        },
    }
