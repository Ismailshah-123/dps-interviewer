import asyncio
import os
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.db.session import get_db
from app.services.retention import purge_old_recordings
from app.services.audit import record_audit
from app.models.models import AuditEvent, Candidate, Interview, ProcessingJob, Recording, StoredDocument, Role, User
from app.services.storage.factory import get_storage

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


@router.get("/storage")
async def storage_library(
    kind: str = Query(default="all", pattern="^(all|recording|pdf)$"),
    q: str | None = Query(default=None, max_length=120),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN.value)),
):
    assets = []
    if kind in {"all", "recording"}:
        stmt = (
            select(Recording, Interview, Candidate)
            .join(Interview, Interview.id == Recording.interview_id)
            .join(Candidate, Candidate.id == Interview.candidate_id)
        )
        if q:
            term = f"%{q.strip()}%"
            stmt = stmt.where(
                Candidate.name.ilike(term)
                | Candidate.reference_number.ilike(term)
                | Recording.original_filename.ilike(term)
            )
        rows = (await db.execute(stmt.order_by(Recording.created_at.desc()).limit(500))).all()
        assets.extend({
            "id": str(record.id), "kind": "recording", "interview_id": str(interview.id),
            "candidate_reference": candidate.reference_number, "candidate_name": candidate.name,
            "filename": record.original_filename, "mime_type": record.mime_type,
            "size_bytes": record.size_bytes, "created_at": record.created_at,
            "version_number": None,
        } for record, interview, candidate in rows)
    if kind in {"all", "pdf"}:
        stmt = (
            select(StoredDocument, Interview, Candidate)
            .join(Interview, Interview.id == StoredDocument.interview_id)
            .join(Candidate, Candidate.id == Interview.candidate_id)
        )
        if q:
            term = f"%{q.strip()}%"
            stmt = stmt.where(
                Candidate.name.ilike(term)
                | Candidate.reference_number.ilike(term)
                | StoredDocument.original_filename.ilike(term)
            )
        rows = (await db.execute(stmt.order_by(StoredDocument.created_at.desc()).limit(500))).all()
        assets.extend({
            "id": str(record.id), "kind": "pdf", "interview_id": str(interview.id),
            "candidate_reference": candidate.reference_number, "candidate_name": candidate.name,
            "filename": record.original_filename, "mime_type": record.mime_type,
            "size_bytes": record.size_bytes, "created_at": record.created_at,
            "version_number": record.version_number,
        } for record, interview, candidate in rows)
    assets.sort(key=lambda item: item["created_at"], reverse=True)
    total = len(assets)
    return {
        "items": assets[skip:skip + limit],
        "meta": {"total": total, "skip": skip, "limit": limit, "has_more": skip + limit < total},
    }


@router.get("/storage/{kind}/{asset_id}/url")
async def storage_asset_playback_url(
    kind: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN.value)),
):
    from uuid import UUID
    if kind not in {"recording", "pdf"}:
        raise HTTPException(status_code=404, detail="Storage item not found")
    try:
        uid = UUID(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Storage item not found") from exc
    item = await db.get(Recording if kind == "recording" else StoredDocument, uid)
    if item is None:
        raise HTTPException(status_code=404, detail="Storage item not found")

    storage = get_storage()
    presign = getattr(storage, "presign_get", None)
    if presign is None:
        return {"url": None, "expires_in": None}
    url = await asyncio.to_thread(presign, item.storage_key, 300)
    await record_audit(
        db,
        actor_user_id=admin.id,
        action="storage.preview_url_issued",
        resource_type=kind,
        resource_id=item.id,
        metadata={"expires_in": 300},
    )
    await db.commit()
    return {"url": url, "expires_in": 300}


@router.get("/storage/{kind}/{asset_id}")
async def stream_storage_asset(
    kind: str,
    asset_id: str,
    request: Request,
    disposition: str = Query(default="inline", pattern="^(inline|attachment)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN.value)),
):
    from uuid import UUID
    if kind not in {"recording", "pdf"}:
        raise HTTPException(status_code=404, detail="Storage item not found")
    try:
        uid = UUID(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Storage item not found") from exc

    if kind == "recording":
        item = await db.get(Recording, uid)
    else:
        item = await db.get(StoredDocument, uid)
    if item is None:
        raise HTTPException(status_code=404, detail="Storage item not found")

    storage = get_storage()
    range_header = request.headers.get("range")
    start, end = 0, None
    partial = False
    if range_header:
        match = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header.strip())
        if not match:
            raise HTTPException(status_code=416, detail="Invalid byte range")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else None
        partial = True

    try:
        if partial:
            body, total_size, last = await asyncio.to_thread(storage.open_range, item.storage_key, start, end)
            length = last - start + 1
        else:
            body = await asyncio.to_thread(storage.open, item.storage_key)
            total_size = item.size_bytes
            length = total_size
            last = total_size - 1
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=416, detail="Requested byte range is not available") from exc

    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", os.path.basename(item.original_filename))[:180] or "download"
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    }
    status_code = 200
    if partial:
        headers["Content-Range"] = f"bytes {start}-{last}/{total_size}"
        status_code = 206

    def chunks():
        try:
            while True:
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    return StreamingResponse(
        chunks(),
        status_code=status_code,
        media_type=item.mime_type,
        headers=headers,
    )
