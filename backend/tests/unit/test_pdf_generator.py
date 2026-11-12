from io import BytesIO

from app.services.pdf.generator import InterviewPDFGenerator, shape_for_pdf

FIELDS = [
    {"field_id": "overview", "label": "Interview Overview", "section": "Overview", "value": {"text": "Synthetic overview.", "source": "ai_summary"}},
    {"field_id": "parent", "label": "Parent Statements", "section": "Discussion", "value": {"text": "والدین نے کہا کہ بچی کو ریاضی پسند ہے۔", "source": "ai_summary"}},
    {"field_id": "mixed", "label": "Mixed", "section": "Discussion", "value": {"text": "She enjoys swimming اور پیانو سیکھ رہی ہے.", "source": "human"}, "human_edited": True},
    {"field_id": "missing", "label": "Follow-up", "section": "Follow-up", "value": {"text": "Not mentioned", "source": "not_mentioned"}},
    {"field_id": "long", "label": "Long answer", "section": "Follow-up", "value": {"text": "Long synthetic sentence about interests. " * 400, "source": "human"}},
]


def _text(pdf: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)


def test_pdf_contains_metadata_labels_and_long_answers():
    pdf = InterviewPDFGenerator().generate("DPS Interview Assessment", "DPS-TEST-1", FIELDS, {"template_name": "Demo", "template_version": "1.0-demo", "status": "finalized", "form_revision": 2, "template_is_placeholder": True})
    assert pdf.startswith(b"%PDF")
    text = _text(pdf)
    for expected in ("DPS-TEST-1", "1.0-demo", "finalized", "PLACEHOLDER TEMPLATE", "Not mentioned", "Entered or edited by staff", "AI-assisted documentation", "must be reviewed by authorized staff"):
        assert expected in text, expected
    # The long answer flows onto further pages instead of being truncated.
    from pypdf import PdfReader
    assert len(PdfReader(BytesIO(pdf)).pages) >= 2
    assert text.count("Long synthetic sentence") > 300


def test_urdu_runs_are_reshaped_but_latin_untouched():
    assert shape_for_pdf("Plain English 123") == "Plain English 123"
    shaped = shape_for_pdf("ریاضی")
    assert shaped != "ریاضی"  # converted to presentation forms and visual order
    assert any("ﭐ" <= ch <= "﻿" for ch in shaped)

def test_additional_conversation_supports_urdu_question_answer_and_evidence():
    exchanges = [
        {
            "question": "اسکول کے اوقات کیا ہیں؟",
            "answer": "اسکول صبح آٹھ بجے شروع ہوتا ہے۔",
            "asked_by": "parent",
            "answered_by": "interviewer",
            "evidence_quotes": ["اسکول کے اوقات کیا ہیں؟"],
        },
        {
            "question": "Does the child enjoy reading?",
            "answer": "Yes, she reads every evening.",
            "asked_by": "interviewer",
            "answered_by": "parent",
            "evidence_quotes": ["Yes, she reads every evening."],
        },
    ]
    pdf = InterviewPDFGenerator().generate(
        "DPS Interview Assessment",
        "DPS-TEST-2",
        FIELDS[:1],
        {"status": "submitted"},
        additional_conversation=exchanges,
    )
    assert pdf.startswith(b"%PDF")
    text = _text(pdf)
    assert "ADDITIONAL CONVERSATION" in text.upper()
    assert "Question asked by: Parent" in text
    assert "Answered by: Interviewer" in text
    assert "Does the child enjoy reading?" in text
    assert "Yes, she reads every evening." in text
    assert "Transcript evidence:" in text
