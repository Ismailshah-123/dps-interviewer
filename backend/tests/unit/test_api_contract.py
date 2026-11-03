from app.schemas.common import CandidatePage, InterviewPage, PaginationMeta

def test_pagination_meta_contract():
    meta = PaginationMeta(total=101, skip=50, limit=50, has_more=True)
    assert meta.has_more is True
    assert meta.total == 101

def test_candidate_page_contract():
    page = CandidatePage(items=[], meta={"total": 0, "skip": 0, "limit": 50, "has_more": False})
    assert page.items == []
    assert page.meta.has_more is False

def test_interview_page_contract():
    page = InterviewPage(items=[], meta={"total": 0, "skip": 0, "limit": 50, "has_more": False})
    assert page.meta.total == 0

from app.schemas.common import UserPage
from app.schemas.common import CandidateUpdate


def test_user_page_is_paginated_contract():
    page = UserPage(items=[], meta={"total": 0, "skip": 0, "limit": 50, "has_more": False})
    assert page.meta.has_more is False


def test_candidate_patch_preserves_explicit_nulls():
    body = CandidateUpdate(assigned_interviewer_id=None)
    assert "assigned_interviewer_id" not in CandidateUpdate().model_dump(exclude_unset=True)
    assert "assigned_interviewer_id" in body.model_dump(exclude_unset=True)


async def test_meta_reports_external_ai(monkeypatch):
    from app.api.meta import meta
    from app.core.config import settings
    monkeypatch.setattr(settings, "summarization_provider", "groq")
    monkeypatch.setattr(settings, "transcription_provider", "faster-whisper")
    assert (await meta())["external_ai"] == ["groq"]
    monkeypatch.setattr(settings, "summarization_provider", "ollama")
    assert (await meta())["external_ai"] == []
