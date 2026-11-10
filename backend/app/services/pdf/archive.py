import hashlib
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    Candidate,
    Interview,
    InterviewForm,
    InterviewFormFieldValue,
    InterviewTemplate,
    InterviewTemplateVersion,
    StoredDocument,
    User,
)
from app.services.audit import record_audit
from app.services.pdf.generator import InterviewPDFGenerator
from app.services.storage.factory import get_storage


async def create_final_interview_pdf(
    db: AsyncSession,
    interview: Interview,
    actor: User,
) -> StoredDocument:
    """Generate and persist a versioned PDF for a finalized interview."""
    if interview.status != "finalized":
        raise ValueError("Only finalized interviews can be archived")

    form = await db.scalar(
        select(InterviewForm).where(InterviewForm.interview_id == interview.id)
    )
    if form is None:
        raise ValueError("Interview form is not available")

    candidate = await db.get(Candidate, interview.candidate_id)
    template = await db.get(InterviewTemplateVersion, form.template_version_id)
    if candidate is None or template is None:
        raise ValueError("Candidate or interview template is unavailable")

    values = (
        await db.scalars(
            select(InterviewFormFieldValue).where(
                InterviewFormFieldValue.form_id == form.id
            )
        )
    ).all()
    by_field = {item.field_id: item for item in values}
    fields = []
    for spec in template.fields:
        item = by_field.get(spec["id"])
        fields.append(
            {
                "field_id": spec["id"],
                "label": spec.get("label", spec["id"]),
                "section": spec.get("section"),
                "value": item.value if item else {"text": "Not mentioned", "source": "not_mentioned"},
                "human_edited": bool(item and item.human_edited),
            }
        )

    parent = await db.get(InterviewTemplate, template.template_id)
    meta = {
        "template_name": parent.name if parent else None,
        "template_version": template.version,
        "status": interview.status,
        "form_revision": form.version_number,
        "template_is_placeholder": bool(
            parent and "placeholder" in (parent.description or "").lower()
        ),
        "submitted_at": interview.submitted_at.strftime("%Y-%m-%d %H:%M UTC")
        if interview.submitted_at
        else None,
        "finalized_at": interview.finalized_at.strftime("%Y-%m-%d %H:%M UTC")
        if interview.finalized_at
        else None,
    }
    data = InterviewPDFGenerator().generate(
        "DPS Interview Assessment", candidate.reference_number, fields, meta
    )
    digest = hashlib.sha256(data).hexdigest()

    existing = await db.scalar(
        select(StoredDocument)
        .where(
            StoredDocument.interview_id == interview.id,
            StoredDocument.document_type == "final_interview_pdf",
            StoredDocument.sha256 == digest,
        )
        .order_by(StoredDocument.version_number.desc())
    )
    if existing is not None:
        return existing

    version = int(
        await db.scalar(
            select(func.max(StoredDocument.version_number)).where(
                StoredDocument.interview_id == interview.id,
                StoredDocument.document_type == "final_interview_pdf",
            )
        )
        or 0
    ) + 1
    filename = f"{candidate.reference_number}-interview-v{version}.pdf"
    key = f"documents/interviews/{interview.id}/{uuid4()}-{filename}"
    storage = get_storage()
    await storage.save_bytes(key, data, "application/pdf")

    document = StoredDocument(
        interview_id=interview.id,
        document_type="final_interview_pdf",
        storage_key=key,
        original_filename=filename,
        mime_type="application/pdf",
        size_bytes=len(data),
        sha256=digest,
        version_number=version,
        created_by=actor.id,
    )
    db.add(document)
    await record_audit(
        db,
        actor_user_id=actor.id,
        action="document.archived",
        resource_type="interview",
        resource_id=interview.id,
        metadata={"document_type": "final_interview_pdf", "version": version, "size_bytes": len(data)},
    )
    return document
