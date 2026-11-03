from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Candidate, User, Role
from app.schemas.common import CandidateCreate, CandidateUpdate, CandidateOut, CandidatePage, PaginationMeta

router = APIRouter(prefix="/candidates", tags=["candidates"])

def can_access(candidate: Candidate, user: User):
    return user.role == Role.ADMIN.value or candidate.assigned_interviewer_id == user.id or user.role == Role.REVIEWER.value

def datetime_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

@router.post("", response_model=CandidateOut, status_code=201)
async def create(body: CandidateCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {Role.ADMIN.value, Role.INTERVIEWER.value}:
        raise HTTPException(status_code=403, detail="Only administrators and interviewers can create candidates")
    if body.assigned_interviewer_id:
        assigned = await db.get(User, body.assigned_interviewer_id)
        if not assigned or assigned.role != Role.INTERVIEWER.value or not assigned.is_active:
            raise HTTPException(status_code=400, detail="Assigned user must be an active interviewer")
    ref = f"DPS-{datetime_now().strftime('%Y%m%d')}-{str(__import__('uuid').uuid4()).replace('-', '')[:8].upper()}"
    candidate = Candidate(reference_number=ref, name=body.name, application_reference=body.application_reference,
                          grade=body.grade, interview_datetime=body.interview_datetime,
                          assigned_interviewer_id=body.assigned_interviewer_id or user.id,
                          metadata_json=body.metadata, created_by=user.id)
    db.add(candidate)
    await db.commit(); await db.refresh(candidate)
    return candidate

@router.get("", response_model=CandidatePage)
async def list_candidates(q: str | None = Query(default=None, max_length=100),
                          skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                          db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    base = select(Candidate)
    count_base = select(func.count(Candidate.id))
    if user.role == Role.INTERVIEWER.value:
        visibility = Candidate.assigned_interviewer_id == user.id
        base = base.where(visibility); count_base = count_base.where(visibility)
    if q:
        pattern = f"%{q}%"
        search = or_(Candidate.name.ilike(pattern), Candidate.reference_number.ilike(pattern), Candidate.application_reference.ilike(pattern))
        base = base.where(search); count_base = count_base.where(search)
    total = int(await db.scalar(count_base) or 0)
    rows = (await db.scalars(base.order_by(Candidate.created_at.desc()).offset(skip).limit(limit))).all()
    return {"items": list(rows), "meta": {"total": total, "skip": skip, "limit": limit, "has_more": skip + len(rows) < total}}

@router.get("/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate or not can_access(candidate, user): raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.patch("/{candidate_id}", response_model=CandidateOut)
async def update_candidate(candidate_id: UUID, body: CandidateUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate or not can_access(candidate, user): raise HTTPException(status_code=404, detail="Candidate not found")
    if user.role == Role.REVIEWER.value: raise HTTPException(status_code=403, detail="Reviewer cannot edit candidates")
    if body.assigned_interviewer_id:
        assigned = await db.get(User, body.assigned_interviewer_id)
        if not assigned or assigned.role != Role.INTERVIEWER.value or not assigned.is_active:
            raise HTTPException(status_code=400, detail="Assigned user must be an active interviewer")
    if user.role == Role.INTERVIEWER.value and body.assigned_interviewer_id not in {None, user.id}:
        raise HTTPException(status_code=403, detail="Interviewers may only assign candidates to themselves")
    values = body.model_dump(exclude_unset=True)
    for field in ("name", "application_reference", "grade", "interview_datetime", "assigned_interviewer_id"):
        if field in values:
            setattr(candidate, field, values[field])
    if "metadata" in values:
        candidate.metadata_json = values["metadata"] or {}
    await db.commit(); await db.refresh(candidate)
    return candidate
