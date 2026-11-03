from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.models import InterviewTemplate, InterviewTemplateVersion, Role, User

router = APIRouter(prefix="/templates", tags=["templates"])
class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    fields: list[dict]

@router.get("")
async def list_templates(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    templates = (await db.scalars(select(InterviewTemplate).order_by(InterviewTemplate.created_at.desc()))).all()
    return [{"id":str(t.id),"name":t.name,"description":t.description,"active":t.active} for t in templates]

@router.post("", status_code=201)
async def create_template(body: TemplateCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN.value))):
    existing = await db.scalar(select(InterviewTemplate).where(InterviewTemplate.name == body.name))
    if existing: raise HTTPException(status_code=409, detail="Template name already exists")
    template = InterviewTemplate(name=body.name, description=body.description); db.add(template); await db.flush()
    version = InterviewTemplateVersion(template_id=template.id, version="1.0", fields=body.fields, is_current=True); db.add(version)
    await db.commit(); return {"template_id":str(template.id),"version_id":str(version.id)}

@router.get("/{template_id}/versions")
async def versions(template_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    rows = (await db.scalars(select(InterviewTemplateVersion).where(InterviewTemplateVersion.template_id == template_id).order_by(InterviewTemplateVersion.created_at.desc()))).all()
    return [{"id":str(v.id),"version":v.version,"fields":v.fields,"is_current":v.is_current} for v in rows]

@router.get("/versions/{version_id}")
async def version_detail(version_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """A specific template version, so historical interviews render with the structure they were created with."""
    v = await db.get(InterviewTemplateVersion, version_id)
    if not v: raise HTTPException(status_code=404, detail="Template version not found")
    t = await db.get(InterviewTemplate, v.template_id)
    return {"id": str(v.id), "template_id": str(v.template_id), "template_name": t.name if t else None,
            "template_description": t.description if t else None, "version": v.version, "fields": v.fields, "is_current": v.is_current}
