"""Shared source-of-truth for preview and archived interview PDFs."""
from app.services.pdf.generator import InterviewPDFGenerator


def build_interview_pdf_data(candidate, interview, form, template, parent, values, summary) -> bytes:
    """Build the exact same PDF bytes for downloads and final archival."""
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
    additional_conversation = (
        (summary.data or {}).get("additional_conversation", []) if summary else []
    )
    return InterviewPDFGenerator().generate(
        "DPS Interview Assessment",
        candidate.reference_number,
        fields,
        meta,
        additional_conversation=additional_conversation,
    )
