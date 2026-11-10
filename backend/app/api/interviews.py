from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.models import Candidate, ConsentRecord, Interview, InterviewForm, InterviewFormFieldValue, InterviewStatus, Role, User, InterviewTemplateVersion
from app.schemas.common import InterviewCreate, InterviewOut, ConsentCreate, InterviewPage, InterviewStats
from app.services.workflow import transition
from app.services.audit import record_audit
from app.services.authorization import assert_interview_access, REVIEW_VISIBLE_STATUSES, REVIEW_ROLES

router = APIRouter(prefix="/interviews", tags=["interviews"])

async def get_owned_interview(interview_id: UUID, db: AsyncSession, user: User):
    interview = await db.get(Interview, interview_id)
    return assert_interview_access(interview, user)


def _scoped(stmt, user: User):
    if user.role == Role.INTERVIEWER.value:
        return stmt.where(Interview.interviewer_id == user.id)
    if user.role in REVIEW_ROLES:
        return stmt.where(Interview.status.in_(list(REVIEW_VISIBLE_STATUSES)))
    return stmt


async def _decorate(db: AsyncSession, interviews: list[Interview]) -> list[InterviewOut]:
    """Attach the candidate reference and consent state the UI needs to label an interview."""
    candidate_ids = {i.candidate_id for i in interviews}
    candidates = {c.id: c for c in (await db.scalars(select(Candidate).where(Candidate.id.in_(candidate_ids)))).all()} if candidate_ids else {}
    ids = [i.id for i in interviews]
    consents = {c.interview_id: c.status for c in (await db.scalars(select(ConsentRecord).where(ConsentRecord.interview_id.in_(ids)))).all()} if ids else {}
    out = []
    for i in interviews:
        c = candidates.get(i.candidate_id)
        out.append(InterviewOut.model_validate(i).model_copy(update={
            "candidate_reference": c.reference_number if c else None,
            "candidate_name": c.name if c else None,
            "candidate_grade": c.grade if c else None,
            "consent_status": consents.get(i.id),
        }))
    return out


@router.post("", response_model=InterviewOut, status_code=201)
async def create_interview(body: InterviewCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    candidate = await db.get(Candidate, body.candidate_id)
    if not candidate: raise HTTPException(status_code=404, detail="Candidate not found")
    if user.role == Role.INTERVIEWER.value and candidate.assigned_interviewer_id not in {None, user.id}:
        raise HTTPException(status_code=403, detail="Candidate is assigned to another interviewer")
    interviewer_id = user.id if user.role == Role.INTERVIEWER.value else candidate.assigned_interviewer_id
    if interviewer_id is None:
        raise HTTPException(status_code=409, detail="An interviewer must be assigned before creating the interview")
    assigned = await db.get(User, interviewer_id)
    if not assigned or assigned.role != Role.INTERVIEWER.value or not assigned.is_active:
        raise HTTPException(status_code=409, detail="Assigned interviewer is not active")
    template_id = body.template_version_id
    if not template_id:
        current = await db.scalar(select(InterviewTemplateVersion).where(InterviewTemplateVersion.is_current.is_(True)).order_by(InterviewTemplateVersion.created_at.desc()))
        template_id = current.id if current else None
    interview = Interview(candidate_id=candidate.id, interviewer_id=interviewer_id, template_version_id=template_id)
    db.add(interview); await db.flush()
    await record_audit(db, actor_user_id=user.id, action="interview.created", resource_type="interview", resource_id=interview.id)
    await db.commit(); await db.refresh(interview); return (await _decorate(db, [interview]))[0]

@router.get("", response_model=InterviewPage)
async def list_interviews(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                          status: list[str] | None = Query(default=None),
                          candidate_id: UUID | None = None,
                          db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    base = _scoped(select(Interview), user)
    count_base = _scoped(select(func.count(Interview.id)), user)
    if status:
        allowed = {x.value for x in InterviewStatus}
        if any(s not in allowed for s in status): raise HTTPException(status_code=400, detail="Invalid interview status")
        base = base.where(Interview.status.in_(status)); count_base = count_base.where(Interview.status.in_(status))
    if candidate_id:
        base = base.where(Interview.candidate_id == candidate_id); count_base = count_base.where(Interview.candidate_id == candidate_id)
    total = int(await db.scalar(count_base) or 0)
    rows = (await db.scalars(base.order_by(Interview.created_at.desc()).offset(skip).limit(limit))).all()
    return {"items": await _decorate(db, list(rows)), "meta": {"total": total, "skip": skip, "limit": limit, "has_more": skip + len(rows) < total}}

@router.get("/stats", response_model=InterviewStats)
async def interview_stats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """System-wide counts by status, limited to the interviews the caller may see."""
    rows = (await db.execute(_scoped(select(Interview.status, func.count(Interview.id)), user).group_by(Interview.status))).all()
    by_status = {status: int(count) for status, count in rows}
    return {"total": sum(by_status.values()), "by_status": by_status}

@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return (await _decorate(db, [await get_owned_interview(interview_id, db, user)]))[0]

@router.post("/{interview_id}/consent")
async def consent(interview_id: UUID, body: ConsentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    interview = await get_owned_interview(interview_id, db, user)
    if interview.interviewer_id != user.id and user.role != Role.ADMIN.value: raise HTTPException(status_code=403, detail="Only assigned interviewer can confirm consent")
    if not body.confirmed:
        raise HTTPException(status_code=400, detail="Required recording consent was not confirmed")
    existing = await db.scalar(select(ConsentRecord).where(ConsentRecord.interview_id == interview.id))
    if existing:
        existing.status="confirmed"
        existing.notice_version=body.notice_version
        existing.confirmed_by=user.id
        existing.confirmed_at=datetime.now(timezone.utc)
        existing.withdrawn_at=None
    else: db.add(ConsentRecord(interview_id=interview.id, status="confirmed", notice_version=body.notice_version, confirmed_by=user.id))
    await record_audit(db, actor_user_id=user.id, action="consent.confirmed", resource_type="interview", resource_id=interview.id, metadata={"notice_version": body.notice_version})
    await db.commit(); return {"status":"confirmed"}

@router.post("/{interview_id}/consent/withdraw")
async def withdraw_consent(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    interview = await get_owned_interview(interview_id, db, user)
    consent = await db.scalar(select(ConsentRecord).where(ConsentRecord.interview_id == interview.id))
    if not consent or consent.status != "confirmed":
        raise HTTPException(status_code=404, detail="Confirmed consent not found")
    consent.status = "withdrawn"
    consent.withdrawn_at = datetime.now(timezone.utc)
    if interview.status in {InterviewStatus.RECORDING.value, InterviewStatus.DRAFT.value}:
        interview.status = InterviewStatus.CANCELLED.value
    await record_audit(db, actor_user_id=user.id, action="consent.withdrawn", resource_type="interview", resource_id=interview.id)
    await db.commit()
    return {"status": "withdrawn", "interview_status": interview.status}


@router.post("/{interview_id}/recording-start")
async def recording_start(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    interview = await get_owned_interview(interview_id, db, user)
    consent = await db.scalar(select(ConsentRecord).where(ConsentRecord.interview_id == interview.id, ConsentRecord.status == "confirmed", ConsentRecord.withdrawn_at.is_(None)))
    if not consent: raise HTTPException(status_code=400, detail="Recording consent is required")
    if interview.status == InterviewStatus.RECORDING.value:
        return {"status": interview.status}  # idempotent: the browser may retry after a reload
    transition(interview, InterviewStatus.RECORDING.value)
    await record_audit(db, actor_user_id=user.id, action="recording.started", resource_type="interview", resource_id=interview.id)
    await db.commit(); return {"status": interview.status}


@router.post("/{interview_id}/submit", response_model=InterviewOut)
async def submit(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles(Role.ADMIN.value, Role.INTERVIEWER.value))):
    interview = await get_owned_interview(interview_id, db, user)
    if interview.status not in {InterviewStatus.NEEDS_REVIEW.value, InterviewStatus.CORRECTION_REQUESTED.value}:
        raise HTTPException(status_code=409, detail="Interview must be awaiting interviewer review or correction before submission")
    form = await db.scalar(select(InterviewForm).where(InterviewForm.interview_id == interview.id))
    if not form: raise HTTPException(status_code=409, detail="Interview form is not ready")
    pending = int(await db.scalar(select(func.count(InterviewFormFieldValue.id)).where(InterviewFormFieldValue.form_id == form.id, InterviewFormFieldValue.review_status == "needs_review")) or 0)
    if pending:
        raise HTTPException(status_code=409, detail=f"{pending} form field(s) still need interviewer confirmation")
    resubmission = interview.status == InterviewStatus.CORRECTION_REQUESTED.value
    if resubmission:
        transition(interview, InterviewStatus.NEEDS_REVIEW.value)
        form.version_number += 1
    transition(interview, InterviewStatus.SUBMITTED.value)
    await record_audit(db, actor_user_id=user.id, action='interview.resubmitted' if resubmission else 'interview.submitted', resource_type='interview', resource_id=interview.id)
    await db.commit(); await db.refresh(interview); return (await _decorate(db, [interview]))[0]
