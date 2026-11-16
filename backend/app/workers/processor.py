
import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.summarization.prompt import clean_summary
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import (
    ProcessingJob,
    Interview,
    Candidate,
    Recording,
    Transcript,
    TranscriptSegment,
    Summary,
    InterviewTemplateVersion,
    InterviewForm,
    InterviewFormFieldValue,
    InterviewStatus,
    ConsentRecord,
)
from app.services.storage.factory import get_storage
from app.services.transcription.factory import get_transcription_provider
from app.services.summarization.factory import get_summarization_provider
from app.services.form_extraction import DPSFormExtractor
from app.services.workflow import transition
from app.services.audit import record_audit
from app.core.observability import (
    job_completed,
    job_failed,
    job_retried,
    job_recovered,
    job_running,
)
from app.services.groq import GroqProviderError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def retry_delay(attempt: int) -> timedelta:
    # Bounded exponential backoff: 15s, 30s, 60s, 120s ... up to 15 minutes.
    seconds = min(
        settings.processing_retry_backoff_seconds
        * (2 ** max(attempt - 1, 0)),
        900,
    )
    return timedelta(seconds=seconds)


class JobCancelled(Exception):
    """Raised internally when an administrator cancels an in-flight job."""


async def _heartbeat_loop(job_id):
    """Keep long-running AI jobs alive while the provider call is in flight."""
    interval = max(10, min(settings.processing_stale_seconds // 3, 60))

    try:
        while True:
            await asyncio.sleep(interval)

            async with SessionLocal() as hb_db:
                job = await hb_db.get(ProcessingJob, job_id)

                if not job or job.status != "running":
                    return

                job.heartbeat_at = utcnow()
                await hb_db.commit()

    except asyncio.CancelledError:
        return


async def _ensure_job_not_cancelled(
    db: AsyncSession,
    job_id,
) -> None:
    row = await db.get(ProcessingJob, job_id)

    if not row or row.status == "cancelled":
        raise JobCancelled()


async def recover_stale_jobs(db: AsyncSession) -> int:
    """Return abandoned running jobs to the queue after a worker crash."""

    cutoff = utcnow() - timedelta(
        seconds=settings.processing_stale_seconds
    )

    rows = (
        await db.scalars(
            select(ProcessingJob)
            .where(
                ProcessingJob.status == "running",
                or_(
                    ProcessingJob.heartbeat_at < cutoff,
                    ProcessingJob.heartbeat_at.is_(None),
                ),
            )
            .order_by(ProcessingJob.created_at)
            .limit(100)
        )
    ).all()

    recovered = 0

    for job in rows:
        if job.attempts < job.max_attempts:
            job.status = "queued"
            job.next_attempt_at = utcnow()
            job.locked_at = None
            job.heartbeat_at = None

            await record_audit(
                db,
                actor_user_id=None,
                action="processing.stale_recovered",
                resource_type="processing_job",
                resource_id=job.id,
                metadata={"attempt": job.attempts},
            )

        else:
            job.status = "failed"
            job.finished_at = utcnow()
            job.locked_at = None
            job.heartbeat_at = None

            interview = await db.get(
                Interview,
                job.interview_id,
            )

            if interview and interview.status not in {
                InterviewStatus.FINALIZED.value,
                InterviewStatus.CANCELLED.value,
            }:
                interview.status = InterviewStatus.FAILED.value

            await record_audit(
                db,
                actor_user_id=None,
                action="processing.stale_failed",
                resource_type="processing_job",
                resource_id=job.id,
                metadata={"attempt": job.attempts},
            )

        job_recovered.labels(job.job_type).inc()
        recovered += 1

    if recovered:
        await db.commit()

    return recovered


class JobProcessor:

    def __init__(self):
        self.storage = get_storage()

    async def claim(
        self,
        db: AsyncSession,
        job_id,
    ) -> ProcessingJob | None:

        """Claim a queued job."""

        now = utcnow()

        query = select(ProcessingJob).where(
            ProcessingJob.id == job_id,
            ProcessingJob.status == "queued",
            or_(
                ProcessingJob.next_attempt_at.is_(None),
                ProcessingJob.next_attempt_at <= now,
            ),
        )

        # FOR UPDATE is ignored by SQLite and effective with PostgreSQL.
        query = query.with_for_update(skip_locked=True)

        job = await db.scalar(query)

        if not job:
            return None

        job.status = "running"
        job.started_at = now
        job.locked_at = now
        job.heartbeat_at = now
        job.attempts += 1

        job_running.inc()

        await db.commit()

        return job

    async def process_one(self, job_id):

        async with SessionLocal() as db:

            job = await self.claim(db, job_id)

            if not job:
                return False

            try:
                await self._execute(db, job)

                if job.status == "cancelled":
                    job.locked_at = None
                    job.heartbeat_at = None
                    job.next_attempt_at = None

                    await db.commit()

                    job_running.dec()
                    return False

                job.status = "completed"
                job.finished_at = utcnow()
                job.locked_at = None
                job.heartbeat_at = None
                job.next_attempt_at = None
                job.error_code = None
                job.error_message = None

                await db.commit()

                job_running.dec()
                job_completed.labels(job.job_type).inc()

                return True

            except asyncio.CancelledError:
                # The API process may be restarting while this job is running.
                # Return the claimed job to the queue instead of leaving it locked
                # until stale-job recovery runs.
                await db.rollback()

                try:
                    interrupted_job = await db.get(ProcessingJob, job_id)
                    if interrupted_job and interrupted_job.status == "running":
                        interrupted_job.status = "queued"
                        interrupted_job.locked_at = None
                        interrupted_job.heartbeat_at = None
                        interrupted_job.next_attempt_at = utcnow()
                        await db.commit()
                except Exception:
                    await db.rollback()

                job_running.dec()
                raise

            except JobCancelled:

                await db.rollback()

                job_running.dec()

                return False

            except Exception as exc:

                job.error_code = type(exc).__name__
                job.error_message = str(exc)[:1000]
                job.finished_at = utcnow()
                job.locked_at = None
                job.heartbeat_at = None

                if job.attempts < job.max_attempts:

                    job.status = "queued"

                    delay = retry_delay(job.attempts)

                    if (
                        isinstance(exc, GroqProviderError)
                        and exc.retry_after_seconds is not None
                        and exc.retryable
                    ):
                        delay = timedelta(
                            seconds=min(
                                max(exc.retry_after_seconds, 0),
                                900,
                            )
                        )

                    job.next_attempt_at = utcnow() + delay

                    action = "processing.retry_scheduled"

                    job_retried.labels(job.job_type).inc()

                else:

                    job.status = "failed"
                    job.next_attempt_at = None

                    interview = await db.get(
                        Interview,
                        job.interview_id,
                    )

                    if interview and interview.status not in {
                        InterviewStatus.FINALIZED.value,
                        InterviewStatus.CANCELLED.value,
                    }:
                        interview.status = InterviewStatus.FAILED.value

                    action = "processing.failed"

                    job_failed.labels(job.job_type).inc()

                await record_audit(
                    db,
                    actor_user_id=None,
                    action=action,
                    resource_type="processing_job",
                    resource_id=job.id,
                    metadata={
                        "attempt": job.attempts,
                        "error_code": job.error_code,
                        "next_attempt_at": (
                            job.next_attempt_at.isoformat()
                            if job.next_attempt_at
                            else None
                        ),
                    },
                )

                await db.commit()

                job_running.dec()

                return False

    async def _execute(
        self,
        db: AsyncSession,
        job: ProcessingJob,
    ):

        interview = await db.get(
            Interview,
            job.interview_id,
        )

        if not interview:
            raise RuntimeError("Interview not found")

        # --------------------------------------------------
        # Find the latest recording
        # --------------------------------------------------

        recording = await db.scalar(
            select(Recording)
            .where(
                Recording.interview_id == interview.id
            )
            .order_by(Recording.created_at.desc())
        )

        if not recording:
            raise RuntimeError("No recording exists for interview")

        # --------------------------------------------------
        # TRANSCRIPTION JOB
        # --------------------------------------------------

        if job.job_type == "transcription":

            consent = await db.scalar(
                select(ConsentRecord).where(
                    ConsentRecord.interview_id == interview.id,
                    ConsentRecord.status == "confirmed",
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )

            if not consent:

                job.status = "cancelled"
                job.finished_at = utcnow()

                interview.status = InterviewStatus.CANCELLED.value

                await record_audit(
                    db,
                    actor_user_id=None,
                    action="processing.cancelled_consent_withdrawn",
                    resource_type="processing_job",
                    resource_id=job.id,
                )

                await db.flush()

                return

            # Restore workflow state for an explicitly retried job.
            if interview.status == InterviewStatus.FAILED.value:
                transition(
                    interview,
                    InterviewStatus.QUEUED.value,
                )

            if interview.status == InterviewStatus.UPLOADED.value:
                transition(
                    interview,
                    InterviewStatus.QUEUED.value,
                )

            if interview.status == InterviewStatus.QUEUED.value:
                transition(
                    interview,
                    InterviewStatus.TRANSCRIBING.value,
                )

            suffix_by_mime = {
                "audio/webm": ".webm",
                "audio/wav": ".wav",
                "audio/mpeg": ".mp3",
                "audio/mp4": ".mp4",
                "audio/x-m4a": ".m4a",
                "audio/ogg": ".ogg",
            }

            suffix = suffix_by_mime.get(
                recording.mime_type,
                ".audio",
            )

            # Temporary file remains alive during transcription.
            with tempfile.TemporaryDirectory(
                prefix="dps-audio-"
            ) as temp_dir:

                audio_path = (
                    Path(temp_dir) / f"recording{suffix}"
                )

                await asyncio.to_thread(
                    self.storage.download_to_path,
                    recording.storage_key,
                    audio_path,
                )

                job.heartbeat_at = utcnow()

                await db.flush()

                provider = get_transcription_provider()

                heartbeat = asyncio.create_task(
                    _heartbeat_loop(job.id)
                )

                try:

                    result = await provider.transcribe(
                        audio_path
                    )

                    await _ensure_job_not_cancelled(
                        db,
                        job.id,
                    )

                finally:

                    heartbeat.cancel()

                    await asyncio.gather(
                        heartbeat,
                        return_exceptions=True,
                    )

            # Temporary audio is now safely removed.
            job.heartbeat_at = utcnow()

            old = await db.scalar(
                select(Transcript).where(
                    Transcript.interview_id == interview.id
                )
            )

            if old:
                await db.delete(old)
                await db.flush()

            transcript = Transcript(
                interview_id=interview.id,
                original_text=result.text,
                language=result.language,
                provider=provider.name,
                model_name=provider.model_name,
                model_version=provider.model_version,
                processing_seconds=result.processing_seconds,
            )

            db.add(transcript)

            await db.flush()

            for segment in result.segments:

                db.add(
                    TranscriptSegment(
                        transcript_id=transcript.id,
                        sequence=segment.sequence,
                        start_seconds=segment.start_seconds,
                        end_seconds=segment.end_seconds,
                        text=segment.text,
                        speaker_label=segment.speaker_label,
                        confidence=segment.confidence,
                    )
                )

            transition(
                interview,
                InterviewStatus.TRANSCRIPT_READY.value,
            )

            summary_key = (
                f"summary:{interview.id}:{transcript.id}"
            )

            existing = await db.scalar(
                select(ProcessingJob).where(
                    ProcessingJob.idempotency_key == summary_key
                )
            )

            if not existing:

                db.add(
                    ProcessingJob(
                        interview_id=interview.id,
                        job_type="summary",
                        status="queued",
                        max_attempts=settings.processing_max_attempts,
                        idempotency_key=summary_key,
                        next_attempt_at=utcnow(),
                    )
                )

            return

        # --------------------------------------------------
        # SUMMARY JOB
        # --------------------------------------------------

        if job.job_type == "summary":

            if interview.status == InterviewStatus.FAILED.value:
                transition(
                    interview,
                    InterviewStatus.TRANSCRIPT_READY.value,
                )

            if interview.status == InterviewStatus.TRANSCRIPT_READY.value:
                transition(
                    interview,
                    InterviewStatus.SUMMARIZING.value,
                )

            transcript = await db.scalar(
                select(Transcript).where(
                    Transcript.interview_id == interview.id
                )
            )

            if not transcript:
                raise RuntimeError(
                    "Transcript is required before summarization"
                )

            segments = (
                await db.scalars(
                    select(TranscriptSegment)
                    .where(
                        TranscriptSegment.transcript_id == transcript.id
                    )
                    .order_by(TranscriptSegment.sequence)
                )
            ).all()

            provider = get_summarization_provider()

            heartbeat = asyncio.create_task(
                _heartbeat_loop(job.id)
            )

            try:

                result = await provider.summarize(
                    transcript.original_text,
                    [
                        {
                            "sequence": s.sequence,
                            "start_seconds": s.start_seconds,
                            "end_seconds": s.end_seconds,
                            "text": s.text,
                        }
                        for s in segments
                    ],
                )

                await _ensure_job_not_cancelled(
                    db,
                    job.id,
                )

            finally:

                heartbeat.cancel()

                await asyncio.gather(
                    heartbeat,
                    return_exceptions=True,
                )

            result = clean_summary(result)

            old = await db.scalar(
                select(Summary).where(
                    Summary.interview_id == interview.id
                )
            )

            if old:

                old.data = result.model_dump()

            else:

                db.add(
                    Summary(
                        interview_id=interview.id,
                        data=result.model_dump(),
                        provider=provider.name,
                        model_name=provider.model_name,
                        prompt_version=provider.prompt_version,
                    )
                )

            template = (
                await db.get(
                    InterviewTemplateVersion,
                    interview.template_version_id,
                )
                if interview.template_version_id
                else None
            )

            if not template:
                raise RuntimeError(
                    "Interview template version is required"
                )

            form_key = (
                f"form-extraction:{interview.id}:{transcript.id}"
            )

            existing = await db.scalar(
                select(ProcessingJob).where(
                    ProcessingJob.idempotency_key == form_key
                )
            )

            if not existing:

                db.add(
                    ProcessingJob(
                        interview_id=interview.id,
                        job_type="form_extraction",
                        status="queued",
                        max_attempts=settings.processing_max_attempts,
                        idempotency_key=form_key,
                        next_attempt_at=utcnow(),
                    )
                )

            return

        # --------------------------------------------------
        # FORM EXTRACTION JOB
        # --------------------------------------------------

        if job.job_type == "form_extraction":

            if interview.status == InterviewStatus.FAILED.value:
                transition(
                    interview,
                    InterviewStatus.SUMMARIZING.value,
                )

            if interview.status != InterviewStatus.SUMMARIZING.value:
                raise RuntimeError(
                    "Interview is not ready for form extraction: "
                    f"{interview.status}"
                )

            transcript = await db.scalar(
                select(Transcript).where(
                    Transcript.interview_id == interview.id
                )
            )

            summary = await db.scalar(
                select(Summary).where(
                    Summary.interview_id == interview.id
                )
            )

            template = (
                await db.get(
                    InterviewTemplateVersion,
                    interview.template_version_id,
                )
                if interview.template_version_id
                else None
            )

            if not transcript or not summary or not template:
                raise RuntimeError(
                    "Transcript, summary and template are required "
                    "before form extraction"
                )

            segments = (
                await db.scalars(
                    select(TranscriptSegment)
                    .where(
                        TranscriptSegment.transcript_id == transcript.id
                    )
                    .order_by(TranscriptSegment.sequence)
                )
            ).all()

            extractor = DPSFormExtractor()

            heartbeat = asyncio.create_task(
                _heartbeat_loop(job.id)
            )

            try:

                result = await extractor.extract(
                    transcript.original_text,
                    summary.data,
                )

                await _ensure_job_not_cancelled(
                    db,
                    job.id,
                )

            finally:

                heartbeat.cancel()

                await asyncio.gather(
                    heartbeat,
                    return_exceptions=True,
                )

            form = await db.scalar(
                select(InterviewForm).where(
                    InterviewForm.interview_id == interview.id
                )
            )

            if not form:

                form = InterviewForm(
                    interview_id=interview.id,
                    template_version_id=template.id,
                )

                db.add(form)

                await db.flush()

            answers = {
                answer.field_id: answer
                for answer in result.answers
            }

            # Keep off-template discussion separate from the school's fixed form fields.
            # The transcript remains the source of truth; empty answers are preserved as unanswered.
            summary_data = dict(summary.data or {})
            summary_data["additional_conversation"] = [
                {
                    "question": item.question.strip(),
                    "answer": item.answer.strip(),
                    "asked_by": item.asked_by,
                    "answered_by": item.answered_by,
                    "evidence_quotes": item.evidence_quotes,
                }
                for item in result.additional_conversation
                if item.question.strip()
            ]
            summary.data = summary_data

            candidate = await db.get(
                Candidate,
                interview.candidate_id,
            )

            system_values = {
                "registration_no": {
                    "text": candidate.reference_number if candidate else "",
                    "source": "system",
                },
                "child_name": {
                    "text": candidate.name if candidate else "",
                    "source": "system",
                },
                "interview_date": {
                    "text": (
                        interview.created_at.strftime("%Y-%m-%d")
                        if interview.created_at
                        else ""
                    ),
                    "source": "system",
                },
                "grade": {
                    "text": (
                        candidate.grade
                        if candidate and candidate.grade
                        else ""
                    ),
                    "source": "system",
                },
            }

            for field in template.fields:

                fid = field["id"]

                existing = await db.scalar(
                    select(InterviewFormFieldValue).where(
                        InterviewFormFieldValue.form_id == form.id,
                        InterviewFormFieldValue.field_id == fid,
                    )
                )

                if existing and existing.human_edited:
                    continue

                if fid in system_values:

                    value = system_values[fid]
                    evidence = []
                    review_status = "reviewed"

                elif field.get("source") == "manual_only":

                    value = {
                        "text": "",
                        "source": "manual_required",
                    }

                    evidence = []
                    review_status = "needs_review"

                else:

                    answer = answers.get(fid)

                    text = (
                        answer.text.strip()
                        if answer and answer.text
                        else ""
                    )

                    value = (
                        {
                            "text": text,
                            "source": "ai_form",
                        }
                        if text
                        else {
                            "text": "",
                            "source": "not_mentioned",
                        }
                    )

                    evidence = (
                        answer.evidence_quotes
                        if answer
                        else []
                    )

                    review_status = "needs_review"

                if existing:

                    existing.generated_value = value
                    existing.value = value
                    existing.evidence = evidence
                    existing.review_status = review_status

                else:

                    db.add(
                        InterviewFormFieldValue(
                            form_id=form.id,
                            field_id=fid,
                            value=value,
                            generated_value=value,
                            evidence=evidence,
                            review_status=review_status,
                        )
                    )

            transition(
                interview,
                InterviewStatus.FORM_DRAFT_READY.value,
            )

            transition(
                interview,
                InterviewStatus.NEEDS_REVIEW.value,
            )

            return

        raise RuntimeError(
            f"Unsupported job type: {job.job_type}"
        )


async def run_pending_jobs_once():

    async with SessionLocal() as db:

        await recover_stale_jobs(db)

        now = utcnow()

        ids = (
            await db.scalars(
                select(ProcessingJob.id)
                .where(
                    ProcessingJob.status == "queued",
                    or_(
                        ProcessingJob.next_attempt_at.is_(None),
                        ProcessingJob.next_attempt_at <= now,
                    ),
                )
                .order_by(ProcessingJob.created_at)
                .limit(settings.processing_worker_batch_size)
            )
        ).all()

    processor = JobProcessor()

    processed = 0

    for job_id in ids:

        if await processor.process_one(job_id):
            processed += 1

    return processed
