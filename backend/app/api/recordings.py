from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Interview, InterviewStatus, Recording, ProcessingJob, Role, User, ConsentRecord
from app.schemas.common import RecordingOut
from app.services.storage.factory import get_storage
from app.services.workflow import transition
from app.services.audit import record_audit
from app.services.authorization import assert_interview_access

router = APIRouter(prefix="/recordings", tags=["recordings"])
storage = get_storage()

@router.post("/{interview_id}", response_model=RecordingOut, status_code=201)
async def upload_recording(interview_id: UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    interview = await db.get(Interview, interview_id)
    assert_interview_access(interview, user, reviewer_queue_only=False)
    # Browsers send parameters such as "audio/webm;codecs=opus"; only the media type matters here.
    mime_type = (file.content_type or "").split(";")[0].strip().lower()
    if mime_type not in settings.allowed_audio_mime_types: raise HTTPException(status_code=415, detail="Unsupported audio MIME type")
    if not (file.filename or "").strip(): raise HTTPException(status_code=400, detail="A recording filename is required")
    consent = await db.scalar(select(ConsentRecord).where(ConsentRecord.interview_id == interview.id, ConsentRecord.status == "confirmed", ConsentRecord.withdrawn_at.is_(None)))
    if not consent:
        raise HTTPException(status_code=400, detail="Confirmed recording consent is required before uploading audio")
    if interview.status not in {InterviewStatus.RECORDING.value, InterviewStatus.DRAFT.value, InterviewStatus.UPLOADED.value, InterviewStatus.FAILED.value}: raise HTTPException(status_code=409, detail=f"Cannot upload in status {interview.status}")
    transition(interview, InterviewStatus.UPLOADING.value) if interview.status != InterviewStatus.UPLOADING.value else None
    import os
    safe_name = os.path.basename(file.filename or 'recording.bin').replace('\\','_').replace('/','_')[:180] or 'recording.bin'
    key = f"interviews/{interview.id}/{uuid4()}-{safe_name}"
    try:
        size, digest, _ = await storage.save_upload(file, key, settings.max_upload_bytes)
    except ValueError as exc:
        interview.status = InterviewStatus.FAILED.value
        await db.commit()
        raise HTTPException(status_code=413, detail=str(exc))
    if not storage.validate_audio_header(key, mime_type):
        storage.delete(key)
        interview.status = InterviewStatus.FAILED.value
        await db.commit()
        raise HTTPException(status_code=415, detail="Audio content does not match the declared MIME type")
    duplicate = await db.scalar(select(Recording).where(Recording.interview_id == interview.id, Recording.sha256 == digest))
    idempotency_key = f"transcription:{interview.id}:{digest}"
    if duplicate:
        storage.delete(key)
        existing_job = await db.scalar(select(ProcessingJob).where(ProcessingJob.idempotency_key == idempotency_key))
        if existing_job and existing_job.status in {"failed", "cancelled"}:
            existing_job.status = "queued"
            existing_job.next_attempt_at = None
            existing_job.finished_at = None
            existing_job.locked_at = None
            existing_job.heartbeat_at = None
            existing_job.error_code = None
            existing_job.error_message = None
            existing_job.attempts = 0
        if interview.status == InterviewStatus.FAILED.value:
            transition(interview, InterviewStatus.QUEUED.value)
        await db.commit()
        return duplicate
    recording = Recording(interview_id=interview.id, storage_key=key, original_filename=(file.filename or "recording"), mime_type=mime_type, size_bytes=size, sha256=digest, created_by=user.id)
    db.add(recording); await db.flush()
    transition(interview, InterviewStatus.UPLOADED.value)
    existing_job = await db.scalar(select(ProcessingJob).where(ProcessingJob.idempotency_key == idempotency_key))
    if existing_job is None:
        job = ProcessingJob(interview_id=interview.id, job_type="transcription", status="queued", max_attempts=settings.processing_max_attempts, idempotency_key=idempotency_key, next_attempt_at=None)
        db.add(job)
    elif existing_job.status in {"failed", "cancelled"}:
        existing_job.status = "queued"
        existing_job.next_attempt_at = None
        existing_job.finished_at = None
        existing_job.locked_at = None
        existing_job.heartbeat_at = None
        existing_job.error_code = None
        existing_job.error_message = None
        existing_job.attempts = 0
    await record_audit(db, actor_user_id=user.id, action="recording.created", resource_type="recording", resource_id=recording.id, metadata={"sha256":digest,"size_bytes":size}); await db.commit(); await db.refresh(recording)
    return recording

@router.get("/{interview_id}/download")
async def download_recording(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from fastapi.responses import StreamingResponse
    interview = await db.get(Interview, interview_id)
    assert_interview_access(interview, user)
    recording = await db.scalar(select(Recording).where(Recording.interview_id == interview_id).order_by(Recording.created_at.desc()))
    if not recording: raise HTTPException(status_code=404, detail="Recording not found")
    return StreamingResponse(storage.open(recording.storage_key), media_type=recording.mime_type, headers={"Content-Disposition": f'attachment; filename="{recording.original_filename}"'})
