from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Candidate, Interview, InterviewForm, InterviewFormFieldValue, InterviewTemplateVersion, Summary, Role, User
from app.schemas.common import FormOut, FormFieldOut, FormFieldUpdate
from app.services.pdf.payload import build_interview_pdf_data
from app.services.audit import record_audit
from app.services.authorization import assert_interview_access, assert_can_edit_interview

router = APIRouter(prefix="/forms", tags=["forms"])

async def access(interview_id, db, user):
    interview = await db.get(Interview, interview_id)
    return assert_interview_access(interview, user)


@router.get("/{interview_id}", response_model=FormOut)
async def get_form(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await access(interview_id, db, user)
    form = await db.scalar(select(InterviewForm).where(InterviewForm.interview_id == interview_id))
    if not form: raise HTTPException(status_code=404, detail="Form not ready")
    fields = (await db.scalars(select(InterviewFormFieldValue).where(InterviewFormFieldValue.form_id == form.id).order_by(InterviewFormFieldValue.field_id))).all()
    return FormOut.model_validate({**form.__dict__, "fields":[FormFieldOut.model_validate(f) for f in fields]})

@router.patch("/{form_id}/fields/{field_id}", response_model=FormFieldOut)
async def update_field(form_id: UUID, field_id: str, body: FormFieldUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    form = await db.get(InterviewForm, form_id)
    if not form: raise HTTPException(status_code=404, detail="Form not found")
    interview = await db.get(Interview, form.interview_id)
    assert_interview_access(interview, user)
    assert_can_edit_interview(interview, user)
    field = await db.scalar(select(InterviewFormFieldValue).where(InterviewFormFieldValue.form_id == form_id, InterviewFormFieldValue.field_id == field_id))
    if not field: raise HTTPException(status_code=404, detail="Field not found")
    text = body.value.get("text")
    if not isinstance(text, str) or len(text) > 20000:
        raise HTTPException(status_code=422, detail="Field value must contain a text string of at most 20000 characters")
    field.value = {"text": text, "source": "human"}; field.human_edited = True; field.review_status = "reviewed"; field.updated_by = user.id
    await record_audit(db, actor_user_id=user.id, action="form.field_edited", resource_type="form_field", resource_id=field.id, metadata={"field_id":field_id})
    await db.commit(); await db.refresh(field); return field

@router.post("/{form_id}/fields/{field_id}/confirm", response_model=FormFieldOut)
async def confirm_field(form_id: UUID, field_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    form = await db.get(InterviewForm, form_id)
    if not form: raise HTTPException(status_code=404, detail="Form not found")
    interview = await db.get(Interview, form.interview_id)
    assert_interview_access(interview, user)
    assert_can_edit_interview(interview, user)
    field = await db.scalar(select(InterviewFormFieldValue).where(InterviewFormFieldValue.form_id == form_id, InterviewFormFieldValue.field_id == field_id))
    if not field: raise HTTPException(status_code=404, detail="Field not found")
    field.review_status = "reviewed"; field.updated_by = user.id
    await record_audit(db, actor_user_id=user.id, action="form.field_confirmed", resource_type="form_field", resource_id=field.id, metadata={"field_id": field_id})
    await db.commit(); await db.refresh(field); return field

@router.get("/{interview_id}/pdf")
async def pdf(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    interview = await access(interview_id, db, user)
    form = await db.scalar(select(InterviewForm).where(InterviewForm.interview_id == interview_id))
    if not form: raise HTTPException(status_code=404, detail="Form not ready")
    candidate = await db.get(Candidate, interview.candidate_id)
    template = await db.get(InterviewTemplateVersion, form.template_version_id)
    if candidate is None or template is None:
        raise HTTPException(status_code=404, detail="Candidate or interview template is unavailable")
    from app.models.models import InterviewTemplate
    parent = await db.get(InterviewTemplate, template.template_id)
    values = (await db.scalars(
        select(InterviewFormFieldValue).where(InterviewFormFieldValue.form_id == form.id)
    )).all()
    summary = await db.scalar(select(Summary).where(Summary.interview_id == interview.id))
    data = build_interview_pdf_data(candidate, interview, form, template, parent, values, summary)
    await record_audit(db, actor_user_id=user.id, action="form.exported", resource_type="interview", resource_id=interview.id, metadata={"format":"pdf"})
    await db.commit()
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition":f'attachment; filename="{candidate.reference_number}-interview.pdf"'})
