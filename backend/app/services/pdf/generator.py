"""Printable interview form.

Layout follows the configured template's field order and sections. This is NOT a reproduction of
the official DPS paper form, which has not been provided; once it is, a dedicated layout (or direct
filling of a fillable PDF/Word original) should replace this generic one.

Urdu: ReportLab does not shape Arabic script, so Urdu runs are reshaped (arabic-reshaper) and
reordered (python-bidi) before drawing with a Unicode font that contains Arabic presentation forms.
That yields legible Naskh-style text, not Nastaliq calligraphy, and complex mixed-direction
paragraphs may still wrap imperfectly. Always inspect real output visually.
"""
import logging
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings

logger = logging.getLogger(__name__)
ARABIC_RUN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF][\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s\u200c\u200d0-9۰-۹،؟.,!:()-]*")

# Fonts with Arabic-script coverage, tried in order. PDF_FONT_PATH overrides.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
BOLD_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

SOURCE_LABEL = {
    "human": "Entered or edited by staff",
    "ai_summary": "AI draft from transcript, confirmed by interviewer",
    "not_mentioned": "Not mentioned in transcript",
    "manual_required": "Interviewer entry",
}


def _register_fonts() -> tuple[str, str, bool]:
    """Return (regular, bold, unicode_capable)."""
    regular = next((p for p in [settings.pdf_font_path, *FONT_CANDIDATES] if p and Path(p).exists()), None)
    if not regular:
        logger.warning("pdf_unicode_font_missing", extra={"event": "pdf.font_missing"})
        return "Helvetica", "Helvetica-Bold", False
    bold = next((p for p in BOLD_CANDIDATES if Path(p).exists()), regular)
    if "DPSUnicode" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DPSUnicode", regular))
        pdfmetrics.registerFont(TTFont("DPSUnicode-Bold", bold))
    return "DPSUnicode", "DPSUnicode-Bold", True


def shape_for_pdf(text: str) -> str:
    """Reshape and visually reorder Urdu runs; leave Latin text untouched."""
    if not ARABIC_RUN.search(text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:  # pragma: no cover - dependency is declared, this is a safety net
        return text
    return ARABIC_RUN.sub(lambda m: get_display(arabic_reshaper.reshape(m.group(0))), text)


def _para_text(text: str) -> str:
    return "<br/>".join(escape(shape_for_pdf(line)) for line in text.split("\n"))


class InterviewPDFGenerator:
    def generate(
        self,
        title: str,
        candidate_ref: str,
        fields: list[dict],
        meta: dict | None = None,
        additional_conversation: list[dict] | None = None,
    ) -> bytes:
        meta = meta or {}
        font, bold, unicode_ok = _register_fonts()
        base = getSampleStyleSheet()
        body = ParagraphStyle("Body", parent=base["BodyText"], fontName=font, fontSize=10, leading=15)
        body_rtl = ParagraphStyle("BodyRTL", parent=body, alignment=TA_RIGHT)
        label = ParagraphStyle("Label", parent=body, fontName=bold, fontSize=10.5, spaceBefore=8, textColor=colors.HexColor("#1e2a44"))
        label_rtl = ParagraphStyle("LabelRTL", parent=label, alignment=TA_RIGHT)
        small = ParagraphStyle("Small", parent=body, fontSize=8, leading=11, textColor=colors.HexColor("#5b6478"))
        section = ParagraphStyle("Section", parent=body, fontName=bold, fontSize=9, leading=12, spaceBefore=14, textColor=colors.HexColor("#5b6478"))
        heading = ParagraphStyle("H", parent=base["Title"], fontName=bold, fontSize=16, leading=20, alignment=0)

        out = BytesIO()
        doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=50,
                                title=f"{title} {candidate_ref}", author="DPS Interview Documentation System")
        story = [Paragraph(escape(title), heading), Spacer(1, 6)]
        rows = [
            ["Candidate reference", candidate_ref],
            ["Template", f"{meta.get('template_name', '—')} (version {meta.get('template_version', '—')})"],
            ["Interview status", str(meta.get("status", "—")).replace("_", " ")],
            ["Form revision", str(meta.get("form_revision", "—"))],
            ["Submitted", meta.get("submitted_at") or "—"],
            ["Finalized", meta.get("finalized_at") or "—"],
        ]
        table = Table([[Paragraph(escape(k), small), Paragraph(escape(str(v)), body)] for k, v in rows], colWidths=[120, 385])
        table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#dfe3ea")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story += [table, Spacer(1, 8)]
        notices = ["AI-assisted documentation. Machine-generated content must be reviewed by authorized staff before it is relied upon. This document is not an assessment score and makes no admission decision."]
        if meta.get("template_is_placeholder"):
            notices.append("PLACEHOLDER TEMPLATE: this layout is not the official DPS interview form.")
        if not unicode_ok:
            notices.append("Urdu text may not display: no Unicode font with Arabic-script support was found on the server.")
        story += [Paragraph(escape(n), small) for n in notices]

        current_section = None
        for field in fields:
            if field.get("section") and field["section"] != current_section:
                current_section = field["section"]
                story.append(Paragraph(escape(current_section.upper()), section))
            story.append(Paragraph(escape(str(field.get("label", field.get("field_id", "Field")))), label))
            value = field.get("value", {})
            text = value.get("text", "") if isinstance(value, dict) else str(value)
            text = str(text or "").strip() or "Not completed"
            story.append(Paragraph(_para_text(text), body_rtl if ARABIC_RUN.match(text) else body))
            source = SOURCE_LABEL.get((value or {}).get("source") if isinstance(value, dict) else None)
            if field.get("human_edited"):
                source = SOURCE_LABEL["human"]
            if source:
                story.append(Paragraph(escape(source), small))

        exchanges = additional_conversation or []
        story.append(Paragraph("ADDITIONAL CONVERSATION (OUTSIDE THE OFFICIAL FORM)", section))
        if not exchanges:
            story.append(Paragraph("No additional question-and-answer exchanges were captured.", body))
        else:
            for index, exchange in enumerate(exchanges, start=1):
                question = str(exchange.get("question") or "").strip()
                answer = str(exchange.get("answer") or "").strip()
                asked_by = str(exchange.get("asked_by") or "unclear").replace("_", " ").title()
                answered_by = str(exchange.get("answered_by") or "unclear").replace("_", " ").title()
                question_style = label_rtl if ARABIC_RUN.search(question) else label
                story.append(Paragraph(_para_text(f"{index}. {question}"), question_style))
                story.append(Paragraph(_para_text(f"Question asked by: {asked_by}"), small))
                story.append(Paragraph(_para_text(f"Answer: {answer or 'No clear answer captured'}"), body_rtl if ARABIC_RUN.search(answer) else body))
                if answered_by != "Unclear":
                    story.append(Paragraph(escape(f"Answered by: {answered_by}"), small))
                quotes = exchange.get("evidence_quotes") or []
                if quotes:
                    evidence_text = "Transcript evidence: " + " | ".join(str(q) for q in quotes)
                    story.append(Paragraph(_para_text(evidence_text), small))

        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def footer(canvas, doc_):
            canvas.saveState()
            canvas.setFont(font, 7.5)
            canvas.setFillColor(colors.HexColor("#5b6478"))
            canvas.drawString(45, 30, f"{candidate_ref} · confidential · generated {generated}")
            canvas.drawRightString(A4[0] - 45, 30, f"Page {doc_.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return out.getvalue()
