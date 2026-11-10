from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.models import Interview, InterviewForm, InterviewFormFieldValue, InterviewReview, InterviewStatus, Role, User
from app.schemas.common import ReviewCreate, ReviewOut
from app.services.workflow import transition
from app.services.audit import record_audit
from app.services.authorization import assert_interview_access, REVIEW_ROLES
from app.services.pdf.archive import create_final_interview_pdf

router = APIRouter(prefix="/reviews", tags=["reviews"])

REVIEWABLE = {
    InterviewStatus.SUBMITTED.value,
    InterviewStatus.PRINCIPAL_REVIEW.value,
    InterviewStatus.CORRECTION_REQUESTED.value,
    InterviewStatus.REVIEWED.value,
}

async def _form_ready_for_review(interview_id: UUID, db: AsyncSession) -> bool:
    form = await db.scalar(select(InterviewForm).where(InterviewForm.interview_id == interview_id))
    if not form:
        return False
    pending = await db.scalar(
        select(InterviewFormFieldValue.id).where(
            InterviewFormFieldValue.form_id == form.id,
            InterviewFormFieldValue.review_status == "needs_review",
        ).limit(1)
    )
    return pending is None

@router.get("/{interview_id}", response_model=list[ReviewOut])
async def review_history(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    assert_interview_access(await db.get(Interview, interview_id), user)
    rows = (await db.execute(
        select(InterviewReview, User.full_name)
        .join(User, User.id == InterviewReview.reviewer_id)
        .where(InterviewReview.interview_id == interview_id)
        .order_by(InterviewReview.created_at.asc())
    )).all()
    return [
        {
            "id": review.id,
            "interview_id": review.interview_id,
            "reviewer_id": review.reviewer_id,
            "reviewer_name": reviewer_name,
            "action": review.action,
            "remarks": review.remarks,
            "recommendation": review.recommendation,
            "status_from": review.status_from,
            "status_to": review.status_to,
            "created_at": review.created_at,
        }
        for review, reviewer_name in rows
    ]


@router.post("/{interview_id}")
async def review(
    interview_id: UUID,
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(*REVIEW_ROLES, Role.ADMIN.value)),
):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status not in REVIEWABLE:
        raise HTTPException(status_code=409, detail=f"Interview is not reviewable in status {interview.status}")

    # 'review' is intentionally a two-step lifecycle operation:
    # submitted -> principal_review -> reviewed.
    if body.action == "review":
        if interview.status == InterviewStatus.SUBMITTED.value:
            target = InterviewStatus.PRINCIPAL_REVIEW.value
        elif interview.status == InterviewStatus.PRINCIPAL_REVIEW.value:
            if not await _form_ready_for_review(interview.id, db):
                raise HTTPException(status_code=409, detail="All form fields must be reviewed before the interview can be marked reviewed")
            target = InterviewStatus.REVIEWED.value
        else:
            raise HTTPException(status_code=409, detail="Interview must be submitted or in principal review")
    elif body.action == "request_correction":
        if interview.status != InterviewStatus.PRINCIPAL_REVIEW.value:
            raise HTTPException(status_code=409, detail="Corrections can only be requested during principal review")
        if not body.remarks:
            raise HTTPException(status_code=422, detail="Correction remarks are required")
        target = InterviewStatus.CORRECTION_REQUESTED.value
    elif body.action == "finalize":
        if interview.status != InterviewStatus.REVIEWED.value:
            raise HTTPException(status_code=409, detail="Interview must be reviewed before finalization")
        target = InterviewStatus.FINALIZED.value
    else:
        raise HTTPException(status_code=422, detail="Unsupported review action")

    previous_status = interview.status
    transition(interview, target)
    db.add(InterviewReview(
        interview_id=interview.id,
        reviewer_id=user.id,
        action=body.action,
        remarks=body.remarks,
        recommendation=body.recommendation,
        status_from=previous_status,
        status_to=target,
    ))
    if body.action == "finalize":
        try:
            await create_final_interview_pdf(db, interview, user)
        except ValueError as exc:
            await db.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    await record_audit(
        db,
        actor_user_id=user.id,
        action=f"review.{body.action}",
        resource_type="interview",
        resource_id=interview.id,
        metadata={"from_status": previous_status, "to_status": target, "recommendation": body.recommendation},
    )
    await db.commit()
    return {"status": interview.status, "action": body.action}
