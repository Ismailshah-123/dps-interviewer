import pytest
from app.models.models import Interview, InterviewStatus
from app.services.workflow import transition

def test_valid_transition():
    i=Interview(candidate_id=__import__('uuid').uuid4(), interviewer_id=__import__('uuid').uuid4(), status=InterviewStatus.DRAFT.value)
    transition(i, InterviewStatus.RECORDING.value)
    assert i.status == InterviewStatus.RECORDING.value

def test_invalid_transition():
    i=Interview(candidate_id=__import__('uuid').uuid4(), interviewer_id=__import__('uuid').uuid4(), status=InterviewStatus.DRAFT.value)
    with pytest.raises(ValueError): transition(i, InterviewStatus.FINALIZED.value)

def test_full_review_lifecycle_transitions():
    i=Interview(candidate_id=__import__('uuid').uuid4(), interviewer_id=__import__('uuid').uuid4(), status=InterviewStatus.NEEDS_REVIEW.value)
    transition(i, InterviewStatus.SUBMITTED.value)
    transition(i, InterviewStatus.PRINCIPAL_REVIEW.value)
    transition(i, InterviewStatus.REVIEWED.value)
    transition(i, InterviewStatus.FINALIZED.value)
    assert i.status == InterviewStatus.FINALIZED.value
    assert i.submitted_at is not None
    assert i.finalized_at is not None


def test_correction_returns_to_needs_review():
    i=Interview(candidate_id=__import__('uuid').uuid4(), interviewer_id=__import__('uuid').uuid4(), status=InterviewStatus.NEEDS_REVIEW.value)
    transition(i, InterviewStatus.SUBMITTED.value)
    transition(i, InterviewStatus.PRINCIPAL_REVIEW.value)
    transition(i, InterviewStatus.CORRECTION_REQUESTED.value)
    transition(i, InterviewStatus.NEEDS_REVIEW.value)
    assert i.status == InterviewStatus.NEEDS_REVIEW.value

def test_review_state_order_is_enforced():
    i=Interview(candidate_id=__import__('uuid').uuid4(), interviewer_id=__import__('uuid').uuid4(), status=InterviewStatus.SUBMITTED.value)
    transition(i, InterviewStatus.PRINCIPAL_REVIEW.value)
    with pytest.raises(ValueError):
        transition(i, InterviewStatus.FINALIZED.value)
