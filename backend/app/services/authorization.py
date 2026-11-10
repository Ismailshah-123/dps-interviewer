from fastapi import HTTPException
from app.models.models import Interview, InterviewStatus, Role, User

REVIEW_VISIBLE_STATUSES = {
    InterviewStatus.SUBMITTED.value,
    InterviewStatus.PRINCIPAL_REVIEW.value,
    InterviewStatus.CORRECTION_REQUESTED.value,
    InterviewStatus.REVIEWED.value,
    InterviewStatus.FINALIZED.value,
}

# Evidence (transcript segments and form fields) may only change before submission
# or while a correction requested by the reviewer is being addressed.
REVIEW_ROLES = {Role.REVIEWER.value, Role.PRINCIPAL.value}

EDITABLE_STATUSES = {
    InterviewStatus.TRANSCRIPT_READY.value,
    InterviewStatus.FORM_DRAFT_READY.value,
    InterviewStatus.NEEDS_REVIEW.value,
    InterviewStatus.CORRECTION_REQUESTED.value,
}


def reviewer_can_access(interview: Interview) -> bool:
    return interview.status in REVIEW_VISIBLE_STATUSES


def interviewer_can_access(interview: Interview, user: User) -> bool:
    return user.role != Role.INTERVIEWER.value or interview.interviewer_id == user.id


def assert_interview_access(interview: Interview | None, user: User, *, reviewer_queue_only: bool = True) -> Interview:
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role == Role.INTERVIEWER.value and interview.interviewer_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    if user.role in REVIEW_ROLES and reviewer_queue_only and not reviewer_can_access(interview):
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


def assert_can_edit_interview(interview: Interview, user: User) -> None:
    if user.role in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Reviewers and principals cannot edit interview evidence")
    if user.role == Role.INTERVIEWER.value and interview.interviewer_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if interview.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"Interview evidence cannot be edited in status {interview.status}")
