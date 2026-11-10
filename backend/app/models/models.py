from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator
from app.db.base import Base

def now_utc(): return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every backend.

    SQLite drops tzinfo on read, which made comparisons such as refresh-token expiry raise
    TypeError. Values are normalised to UTC on write and re-tagged as UTC on read.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

class Role(StrEnum):
    ADMIN = "administrator"
    INTERVIEWER = "interviewer"
    REVIEWER = "reviewer"  # Legacy role retained for existing accounts.
    PRINCIPAL = "principal"

class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(32), default=Role.INTERVIEWER.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    used_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)

class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)

class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    reference_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    application_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interview_datetime: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    assigned_interviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)
    __table_args__ = (Index("ix_candidates_name_ref", "name", "reference_number"),)

class InterviewStatus(StrEnum):
    DRAFT = "draft"
    RECORDING = "recording"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    TRANSCRIPT_READY = "transcript_ready"
    SUMMARIZING = "summarizing"
    FORM_DRAFT_READY = "form_draft_ready"
    NEEDS_REVIEW = "needs_review"
    SUBMITTED = "submitted"
    PRINCIPAL_REVIEW = "principal_review"
    CORRECTION_REQUESTED = "correction_requested"
    REVIEWED = "reviewed"
    FINALIZED = "finalized"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Interview(Base):
    __tablename__ = "interviews"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(ForeignKey("candidates.id", ondelete="RESTRICT"), index=True)
    interviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(40), default=InterviewStatus.DRAFT.value, index=True)
    template_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("interview_template_versions.id", ondelete="SET NULL"), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)
    __table_args__ = (Index("ix_interviews_reviewer_queue", "status", "created_at"),)

class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), unique=True)
    status: Mapped[str] = mapped_column(String(32))
    notice_version: Mapped[str] = mapped_column(String(64))
    confirmed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    withdrawn_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

class Recording(Base):
    __tablename__ = "recordings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    job_type: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True, index=True)
    locked_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True, index=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    __table_args__ = (Index("ix_processing_job_work", "status", "job_type", "created_at"), Index("ix_processing_job_due", "status", "next_attempt_at", "created_at"))

class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), unique=True)
    original_text: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(150))
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    transcript_id: Mapped[UUID] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    start_seconds: Mapped[float] = mapped_column()
    end_seconds: Mapped[float] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    speaker_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    is_human_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("transcript_id", "sequence", name="uq_transcript_segment_sequence"),)

class Summary(Base):
    __tablename__ = "summaries"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), unique=True)
    data: Mapped[dict] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(150))
    prompt_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)

class InterviewTemplate(Base):
    __tablename__ = "interview_templates"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)

class InterviewTemplateVersion(Base):
    __tablename__ = "interview_template_versions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("interview_templates.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(64))
    fields: Mapped[list] = mapped_column(JSON, default=list)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_template_version"),)

class InterviewForm(Base):
    __tablename__ = "interview_forms"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), unique=True)
    template_version_id: Mapped[UUID] = mapped_column(ForeignKey("interview_template_versions.id"))
    status: Mapped[str] = mapped_column(String(40), default="draft")
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)

class InterviewFormFieldValue(Base):
    __tablename__ = "interview_form_field_values"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    form_id: Mapped[UUID] = mapped_column(ForeignKey("interview_forms.id", ondelete="CASCADE"), index=True)
    field_id: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String(32), default="needs_review")
    human_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, onupdate=now_utc)
    __table_args__ = (UniqueConstraint("form_id", "field_id", name="uq_form_field"),)

class InterviewReview(Base):
    __tablename__ = "interview_reviews"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    interview_id: Mapped[UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64))
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, index=True)

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), index=True)
    success: Mapped[bool] = mapped_column(Boolean)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now_utc, index=True)
