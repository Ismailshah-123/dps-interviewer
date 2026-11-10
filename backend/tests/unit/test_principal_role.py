from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.models import Role
from app.services.authorization import assert_can_edit_interview, assert_interview_access


@pytest.mark.parametrize("role", [Role.PRINCIPAL.value, Role.REVIEWER.value])
def test_review_roles_can_access_submitted_interviews(role):
    interview = SimpleNamespace(status="submitted", interviewer_id=uuid4())
    user = SimpleNamespace(role=role, id=uuid4())

    assert assert_interview_access(interview, user) is interview


@pytest.mark.parametrize("role", [Role.PRINCIPAL.value, Role.REVIEWER.value])
def test_review_roles_cannot_edit_interview_evidence(role):
    interview = SimpleNamespace(status="principal_review", interviewer_id=uuid4())
    user = SimpleNamespace(role=role, id=uuid4())

    with pytest.raises(HTTPException) as exc:
        assert_can_edit_interview(interview, user)

    assert exc.value.status_code == 403


def test_principal_role_is_distinct_from_legacy_reviewer_role():
    assert Role.PRINCIPAL.value == "principal"
    assert Role.REVIEWER.value == "reviewer"
    assert Role.PRINCIPAL.value != Role.REVIEWER.value
