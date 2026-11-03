from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Interview, Summary, Role, User
from app.schemas.common import SummaryOut
from app.services.authorization import assert_interview_access

router=APIRouter(prefix='/summaries',tags=['summaries'])
@router.get('/{interview_id}',response_model=SummaryOut)
async def get_summary(interview_id:UUID,db:AsyncSession=Depends(get_db),user:User=Depends(get_current_user)):
    interview=await db.get(Interview,interview_id)
    if not interview or (user.role==Role.INTERVIEWER.value and interview.interviewer_id!=user.id): raise HTTPException(404,'Interview not found')
    if user.role==Role.REVIEWER.value and interview.status not in {'submitted','principal_review','correction_requested','reviewed','finalized'}: raise HTTPException(403,'Interview is not available for review')
    summary=await db.scalar(select(Summary).where(Summary.interview_id==interview_id))
    if not summary: raise HTTPException(404,'Summary not ready')
    return summary
