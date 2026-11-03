"""PostgreSQL-only acceptance tests for V12 concurrency guarantees.

Run with DPS_TEST_DATABASE_URL pointing at a disposable PostgreSQL database.
These tests are intentionally skipped when PostgreSQL is not provisioned.
"""
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
DB_URL = os.getenv("DPS_TEST_DATABASE_URL")
if not DB_URL:
    pytest.skip("DPS_TEST_DATABASE_URL is not configured", allow_module_level=True)

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.models import Candidate, Interview, ProcessingJob, Role, User
from app.workers.processor import JobProcessor


@pytest.fixture(scope="module")
def pg_engine():
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    yield engine


@pytest.fixture(scope="module")
def pg_sessions(pg_engine):
    return async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)


async def _cleanup(sessions, interview_id, candidate_id, user_id):
    async with sessions() as db:
        await db.execute(delete(ProcessingJob).where(ProcessingJob.interview_id == interview_id))
        await db.execute(delete(Interview).where(Interview.id == interview_id))
        await db.execute(delete(Candidate).where(Candidate.id == candidate_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


@pytest.mark.asyncio
async def test_two_workers_cannot_claim_same_job(pg_sessions):
    user = User(
        id=uuid4(), email=f"v12-{uuid4()}@example.test", full_name="V12", role=Role.ADMIN.value
    )
    candidate = Candidate(
        id=uuid4(), reference_number=f"V12-{uuid4().hex[:12]}", name="Concurrency Candidate", created_by=user.id
    )
    interview = Interview(id=uuid4(), candidate_id=candidate.id, interviewer_id=user.id, status="queued")
    job = ProcessingJob(
        id=uuid4(), interview_id=interview.id, job_type="transcription", status="queued",
        max_attempts=3, next_attempt_at=datetime.now(timezone.utc)
    )

    async with pg_sessions() as db:
        db.add_all([user, candidate, interview, job])
        await db.commit()

    async def attempt_claim():
        processor = JobProcessor()
        async with pg_sessions() as db:
            claimed = await processor.claim(db, job.id)
            return claimed.id if claimed else None

    try:
        first, second = await asyncio.gather(attempt_claim(), attempt_claim())
        assert sorted(x is not None for x in (first, second)) == [False, True]
        async with pg_sessions() as db:
            row = await db.get(ProcessingJob, job.id)
            assert row is not None
            assert row.status == "running"
            assert row.attempts == 1
    finally:
        await _cleanup(pg_sessions, interview.id, candidate.id, user.id)


@pytest.mark.asyncio
async def test_idempotency_key_is_unique(pg_sessions):
    user = User(
        id=uuid4(), email=f"v12-idem-{uuid4()}@example.test", full_name="V12", role=Role.ADMIN.value
    )
    candidate = Candidate(
        id=uuid4(), reference_number=f"V12I-{uuid4().hex[:12]}", name="Idempotency Candidate", created_by=user.id
    )
    interview = Interview(id=uuid4(), candidate_id=candidate.id, interviewer_id=user.id, status="queued")
    key = f"v12:{uuid4()}"

    async with pg_sessions() as db:
        db.add_all([user, candidate, interview])
        await db.commit()

    async def insert_job():
        async with pg_sessions() as db:
            db.add(ProcessingJob(interview_id=interview.id, job_type="summary", idempotency_key=key))
            try:
                await db.commit()
                return True
            except Exception:
                await db.rollback()
                return False

    try:
        results = await asyncio.gather(insert_job(), insert_job())
        assert sum(results) == 1
        async with pg_sessions() as db:
            rows = (await db.scalars(select(ProcessingJob).where(ProcessingJob.idempotency_key == key))).all()
            assert len(rows) == 1
    finally:
        await _cleanup(pg_sessions, interview.id, candidate.id, user.id)
