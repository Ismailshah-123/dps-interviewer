from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Interview, InterviewStatus

ALLOWED = {
    InterviewStatus.DRAFT.value: {InterviewStatus.RECORDING.value, InterviewStatus.UPLOADING.value, InterviewStatus.UPLOADED.value, InterviewStatus.CANCELLED.value},
    InterviewStatus.RECORDING.value: {InterviewStatus.UPLOADING.value, InterviewStatus.CANCELLED.value},
    InterviewStatus.UPLOADING.value: {InterviewStatus.UPLOADED.value, InterviewStatus.FAILED.value},
    InterviewStatus.UPLOADED.value: {InterviewStatus.QUEUED.value, InterviewStatus.FAILED.value},
    InterviewStatus.QUEUED.value: {InterviewStatus.TRANSCRIBING.value, InterviewStatus.FAILED.value},
    InterviewStatus.TRANSCRIBING.value: {InterviewStatus.TRANSCRIPT_READY.value, InterviewStatus.FAILED.value},
    InterviewStatus.TRANSCRIPT_READY.value: {InterviewStatus.SUMMARIZING.value, InterviewStatus.FAILED.value},
    InterviewStatus.SUMMARIZING.value: {InterviewStatus.FORM_DRAFT_READY.value, InterviewStatus.FAILED.value},
    InterviewStatus.FORM_DRAFT_READY.value: {InterviewStatus.NEEDS_REVIEW.value, InterviewStatus.FAILED.value},
    InterviewStatus.NEEDS_REVIEW.value: {InterviewStatus.SUBMITTED.value},
    InterviewStatus.SUBMITTED.value: {InterviewStatus.PRINCIPAL_REVIEW.value},
    InterviewStatus.PRINCIPAL_REVIEW.value: {InterviewStatus.CORRECTION_REQUESTED.value, InterviewStatus.REVIEWED.value},
    InterviewStatus.CORRECTION_REQUESTED.value: {InterviewStatus.NEEDS_REVIEW.value},
    InterviewStatus.REVIEWED.value: {InterviewStatus.FINALIZED.value},
    InterviewStatus.FINALIZED.value: set(),
    InterviewStatus.FAILED.value: {InterviewStatus.QUEUED.value, InterviewStatus.UPLOADING.value, InterviewStatus.CANCELLED.value},
    InterviewStatus.CANCELLED.value: set(),
}

class InvalidTransition(ValueError):
    """Raised when a lifecycle change is not allowed; the API maps it to HTTP 409."""


def transition(interview: Interview, target: str):
    allowed = ALLOWED.get(interview.status, set())
    if target not in allowed:
        raise InvalidTransition(f"Invalid interview transition: {interview.status} -> {target}")
    interview.status = target
    if target == InterviewStatus.SUBMITTED.value:
        interview.submitted_at = datetime.now(timezone.utc)
    if target == InterviewStatus.FINALIZED.value:
        interview.finalized_at = datetime.now(timezone.utc)
