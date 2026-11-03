from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Interview, Transcript, TranscriptSegment, Role, User
from app.schemas.common import TranscriptOut, TranscriptSegmentOut
from app.services.audit import record_audit
from app.services.authorization import assert_interview_access, assert_can_edit_interview

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])
class SegmentEdit(BaseModel):
    text: str
    speaker_label: str | None = None

@router.get("/{interview_id}", response_model=TranscriptOut)
async def get_transcript(interview_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    interview = await db.get(Interview, interview_id)
    assert_interview_access(interview, user)
    transcript = await db.scalar(select(Transcript).where(Transcript.interview_id == interview_id))
    if not transcript: raise HTTPException(status_code=404, detail="Transcript not ready")
    segments = (await db.scalars(select(TranscriptSegment).where(TranscriptSegment.transcript_id == transcript.id).order_by(TranscriptSegment.sequence))).all()
    return TranscriptOut.model_validate({**transcript.__dict__, "segments":[TranscriptSegmentOut.model_validate(s) for s in segments]})

@router.patch("/segments/{segment_id}", response_model=TranscriptSegmentOut)
async def edit_segment(segment_id: UUID, body: SegmentEdit, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    segment = await db.get(TranscriptSegment, segment_id)
    if not segment: raise HTTPException(status_code=404, detail="Segment not found")
    transcript = await db.get(Transcript, segment.transcript_id); interview = await db.get(Interview, transcript.interview_id)
    assert_interview_access(interview, user)
    assert_can_edit_interview(interview, user)
    if len(body.text) > 20000: raise HTTPException(status_code=422, detail="Segment text is too long")
    if segment.original_text is None: segment.original_text = segment.text
    segment.text = body.text; segment.speaker_label = body.speaker_label; segment.is_human_edited = True
    await record_audit(db, actor_user_id=user.id, action="transcript.segment_edited", resource_type="transcript_segment", resource_id=segment.id, metadata={"sequence":segment.sequence})
    await db.commit(); await db.refresh(segment); return segment
