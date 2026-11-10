from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Message(BaseModel):
    message: str

class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int
    has_more: bool

class CandidatePage(BaseModel):
    items: list["CandidateOut"]
    meta: PaginationMeta

class InterviewPage(BaseModel):
    items: list["InterviewOut"]
    meta: PaginationMeta

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserPage(BaseModel):
    items: list["UserOut"]
    meta: PaginationMeta

class UserOut(ORMModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime | None = None

class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    application_reference: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    interview_datetime: datetime | None = None
    assigned_interviewer_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)

class CandidateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    application_reference: str | None = Field(default=None, max_length=100)
    grade: str | None = Field(default=None, max_length=100)
    interview_datetime: datetime | None = None
    assigned_interviewer_id: UUID | None = None
    metadata: dict | None = None

class CandidateOut(ORMModel):
    id: UUID
    reference_number: str
    name: str
    application_reference: str | None
    grade: str | None
    interview_datetime: datetime | None
    assigned_interviewer_id: UUID | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

class InterviewCreate(BaseModel):
    candidate_id: UUID
    template_version_id: UUID | None = None

class InterviewOut(ORMModel):
    id: UUID
    candidate_id: UUID
    interviewer_id: UUID
    status: str
    template_version_id: UUID | None
    submitted_at: datetime | None
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime
    candidate_reference: str | None = None
    candidate_name: str | None = None
    candidate_grade: str | None = None
    consent_status: str | None = None

class InterviewStats(BaseModel):
    total: int
    by_status: dict[str, int]

class ReviewOut(ORMModel):
    id: UUID
    interview_id: UUID
    reviewer_id: UUID
    action: str
    remarks: str | None
    recommendation: str | None
    status_from: str | None = None
    status_to: str | None = None
    reviewer_name: str | None = None
    created_at: datetime

class ConsentCreate(BaseModel):
    notice_version: str = Field(min_length=1, max_length=64)
    confirmed: bool

class RecordingOut(ORMModel):
    id: UUID
    interview_id: UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    duration_seconds: int | None
    created_at: datetime

class TranscriptSegmentOut(ORMModel):
    id: UUID
    sequence: int
    start_seconds: float
    end_seconds: float
    text: str
    speaker_label: str | None
    confidence: float | None
    is_human_edited: bool

class TranscriptOut(ORMModel):
    id: UUID
    interview_id: UUID
    original_text: str
    language: str | None
    provider: str
    model_name: str
    model_version: str | None
    processing_seconds: int | None
    created_at: datetime
    segments: list[TranscriptSegmentOut] = []

class SummaryOut(ORMModel):
    id: UUID
    interview_id: UUID
    data: dict
    provider: str
    model_name: str
    prompt_version: str
    created_at: datetime
    updated_at: datetime

class ReviewCreate(BaseModel):
    action: str = Field(pattern="^(request_correction|review|finalize)$")
    remarks: str | None = None
    recommendation: str | None = Field(default=None, max_length=100)

class FormFieldUpdate(BaseModel):
    value: dict

class FormFieldOut(ORMModel):
    id: UUID
    field_id: str
    value: dict
    generated_value: dict | None
    evidence: list
    review_status: str
    human_edited: bool
    updated_at: datetime

class FormOut(ORMModel):
    id: UUID
    interview_id: UUID
    template_version_id: UUID
    status: str
    version_number: int
    created_at: datetime
    updated_at: datetime
    fields: list[FormFieldOut] = []
