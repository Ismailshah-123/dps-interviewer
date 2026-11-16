from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Candidate, Interview, InterviewForm, InterviewFormFieldValue, InterviewTemplateVersion, Summary, Role, User
from app.schemas.common import FormOut, FormFieldOut, FormFieldUpdate
from app.services.pdf.generator import InterviewPDFGenerator
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
    fields = []
    values = {f.field_id:f for f in (await db.scalars(select(InterviewFormFieldValue).where(InterviewFormFieldValue.form_id == form.id))).all()}
    for spec in template.fields:
        item = values.get(spec["id"])
        fields.append({"field_id": spec["id"], "label": spec.get("label", spec["id"]), "section": spec.get("section"),
                       "value": item.value if item else {"text": "Not mentioned", "source": "not_mentioned"},
                       "human_edited": bool(item and item.human_edited)})
    from app.models.models import InterviewTemplate
    parent = await db.get(InterviewTemplate, template.template_id)
    meta = {"template_name": parent.name if parent else None, "template_version": template.version, "status": interview.status,
            "form_revision": form.version_number,
            "template_is_placeholder": bool(parent and "placeholder" in (parent.description or "").lower()),
            "submitted_at": interview.submitted_at.strftime("%Y-%m-%d %H:%M UTC") if interview.submitted_at else None,
            "finalized_at": interview.finalized_at.strftime("%Y-%m-%d %H:%M UTC") if interview.finalized_at else None}
    await record_audit(db, actor_user_id=user.id, action="form.exported", resource_type="interview", resource_id=interview.id, metadata={"format":"pdf"})
    await db.commit()
    summary = await db.scalar(select(Summary).where(Summary.interview_id == interview.id))
    additional_conversation = (summary.data or {}).get("additional_conversation", []) if summary else []
    data = InterviewPDFGenerator().generate(
        "DPS Interview Assessment",
        candidate.reference_number,
        fields,
        meta,
        additional_conversation=additional_conversation,
    )
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition":f'attachment; filename="{candidate.reference_number}-interview.pdf"'})
