from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.models.models import InterviewStatus, Role
from app.services.authorization import assert_can_edit_interview, assert_interview_access


def user(role, user_id=None):
    return SimpleNamespace(role=role, id=user_id or uuid4())


def interview(interviewer_id, status=InterviewStatus.DRAFT.value):
    return SimpleNamespace(interviewer_id=interviewer_id, status=status)


def test_interviewer_cannot_access_other_interview():
    owner = user(Role.INTERVIEWER.value)
    other = user(Role.INTERVIEWER.value)
    with pytest.raises(HTTPException) as exc:
        assert_interview_access(interview(owner.id), other)
    assert exc.value.status_code == 404


def test_reviewer_cannot_access_draft_interview():
    reviewer = user(Role.REVIEWER.value)
    with pytest.raises(HTTPException) as exc:
        assert_interview_access(interview(uuid4(), InterviewStatus.DRAFT.value), reviewer)
    assert exc.value.status_code == 404


def test_reviewer_can_access_principal_review():
    reviewer = user(Role.REVIEWER.value)
    result = assert_interview_access(interview(uuid4(), InterviewStatus.PRINCIPAL_REVIEW.value), reviewer)
    assert result.status == InterviewStatus.PRINCIPAL_REVIEW.value


def test_reviewer_cannot_edit_evidence():
    reviewer = user(Role.REVIEWER.value)
    with pytest.raises(HTTPException) as exc:
        assert_can_edit_interview(interview(uuid4(), InterviewStatus.PRINCIPAL_REVIEW.value), reviewer)
    assert exc.value.status_code == 403


def test_interviewer_cannot_edit_finalized_interview():
    owner = user(Role.INTERVIEWER.value)
    with pytest.raises(HTTPException) as exc:
        assert_can_edit_interview(interview(owner.id, InterviewStatus.FINALIZED.value), owner)
    assert exc.value.status_code == 409


def test_admin_can_access_and_edit_before_submission():
    admin = user(Role.ADMIN.value)
    item = interview(uuid4(), InterviewStatus.NEEDS_REVIEW.value)
    assert assert_interview_access(item, admin) is item
    assert_can_edit_interview(item, admin)


@pytest.mark.parametrize("status", [InterviewStatus.SUBMITTED.value, InterviewStatus.PRINCIPAL_REVIEW.value, InterviewStatus.REVIEWED.value])
def test_nobody_edits_evidence_after_submission(status):
    for role in (Role.ADMIN.value, Role.INTERVIEWER.value):
        actor = user(role)
        with pytest.raises(HTTPException) as exc:
            assert_can_edit_interview(interview(actor.id, status), actor)
        assert exc.value.status_code == 409


def test_interviewer_can_edit_during_correction():
    owner = user(Role.INTERVIEWER.value)
    assert_can_edit_interview(interview(owner.id, InterviewStatus.CORRECTION_REQUESTED.value), owner)
