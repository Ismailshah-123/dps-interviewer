from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.db.session import get_db
from app.services.retention import purge_old_recordings
from app.services.audit import record_audit
from app.models.models import AuditEvent, ProcessingJob, Role, User

router = APIRouter(prefix="/admin", tags=["admin"])
@router.get("/jobs")
async def jobs(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), status: str | None = Query(default=None, max_length=30), db: AsyncSession = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN.value))):
    stmt = select(ProcessingJob); count_stmt = select(func.count(ProcessingJob.id))
    if status:
        stmt = stmt.where(ProcessingJob.status == status); count_stmt = count_stmt.where(ProcessingJob.status == status)
    total = int(await db.scalar(count_stmt) or 0)
    rows = (await db.scalars(stmt.order_by(ProcessingJob.created_at.desc()).offset(skip).limit(limit))).all()
    items = [{"id":str(j.id),"interview_id":str(j.interview_id),"type":j.job_type,"status":j.status,"attempts":j.attempts,"max_attempts":j.max_attempts,"next_attempt_at":j.next_attempt_at,"error":j.error_message} for j in rows]
    return {"items": items, "meta": {"total": total, "skip": skip, "limit": limit, "has_more": skip + len(items) < total}}

@router.get("/audit")
async def audit(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), action: str | None = Query(default=None, max_length=100), db: AsyncSession = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN.value))):
    stmt = select(AuditEvent); count_stmt = select(func.count(AuditEvent.id))
    if action:
        stmt = stmt.where(AuditEvent.action == action); count_stmt = count_stmt.where(AuditEvent.action == action)
    total = int(await db.scalar(count_stmt) or 0)
    rows = (await db.scalars(stmt.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit))).all()
    items = [{"id":str(x.id),"actor_user_id":str(x.actor_user_id) if x.actor_user_id else None,"action":x.action,"resource_type":x.resource_type,"resource_id":x.resource_id,"created_at":x.created_at} for x in rows]
    return {"items": items, "meta": {"total": total, "skip": skip, "limit": limit, "has_more": skip + len(items) < total}}


@router.post("/retention/purge-recordings")
async def purge_recordings(dry_run: bool = True, admin: User = Depends(require_roles(Role.ADMIN.value))):
    result = await purge_old_recordings(dry_run=dry_run)
    return result


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles(Role.ADMIN.value))):
    from uuid import UUID
    from datetime import datetime, timezone
    try:
        uid = UUID(job_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid job id")
    job = await db.get(ProcessingJob, uid)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in {"failed", "cancelled"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=f"Cannot retry job in status {job.status}")
    job.status = "queued"
    job.next_attempt_at = datetime.now(timezone.utc)
    job.locked_at = None
    job.heartbeat_at = None
    job.error_code = None
    job.error_message = None
    job.finished_at = None
    job.attempts = 0
    await record_audit(db, actor_user_id=admin.id, action="processing.admin_retry", resource_type="processing_job", resource_id=job.id)
    await db.commit()
    return {"id": str(job.id), "status": job.status, "message": "Job requeued"}
