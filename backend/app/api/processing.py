from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.models import Interview, ProcessingJob, Role, User
from app.workers.processor import run_pending_jobs_once
from app.services.authorization import assert_interview_access

router = APIRouter(prefix="/processing", tags=["processing"])

@router.get("/{interview_id}")
async def status(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    interview = await db.get(Interview, interview_id)
    assert_interview_access(interview, user)
    jobs = (await db.scalars(select(ProcessingJob).where(ProcessingJob.interview_id == interview_id).order_by(ProcessingJob.created_at.desc()))).all()
    return {"interview_status": interview.status, "jobs":[{"id":str(j.id),"type":j.job_type,"status":j.status,"attempts":j.attempts,"error":j.error_message} for j in jobs]}

@router.post("/run-once")
async def run_once(_: User = Depends(require_roles(Role.ADMIN.value))):
    await run_pending_jobs_once(); return {"message":"Pending jobs processed"}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles(Role.ADMIN.value))):
    job = await db.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in {"completed", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"Cannot cancel job in status {job.status}")
    job.status = "cancelled"
    job.finished_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    job.next_attempt_at = None
    job.locked_at = None
    job.heartbeat_at = None
    await db.commit()
    return {"id": str(job.id), "status": job.status, "message": "Job cancelled"}
