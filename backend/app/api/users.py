from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.models import User, Role
from app.services.audit import record_audit
from app.services.auth import create_user
from app.schemas.common import UserPage

router=APIRouter(prefix='/users', tags=['users'])
class UserUpdate(BaseModel):
    full_name: str|None=Field(default=None,min_length=1,max_length=200)
    role: str|None=None
    is_active: bool|None=None

@router.get('', response_model=UserPage)
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), role: str | None = Query(default=None, max_length=30), db: AsyncSession=Depends(get_db), _:User=Depends(require_roles(Role.ADMIN.value))):
    stmt = select(User); count_stmt = select(func.count(User.id))
    if role:
        if role not in {r.value for r in Role}: raise HTTPException(400, 'Invalid role')
        stmt = stmt.where(User.role == role); count_stmt = count_stmt.where(User.role == role)
    total = int(await db.scalar(count_stmt) or 0)
    rows=(await db.scalars(stmt.order_by(User.created_at.desc()).offset(skip).limit(limit))).all()
    items = [{'id':str(u.id),'email':u.email,'full_name':u.full_name,'role':u.role,'is_active':u.is_active,'created_at':u.created_at} for u in rows]
    return {'items': items, 'meta': {'total': total, 'skip': skip, 'limit': limit, 'has_more': skip + len(items) < total}}

@router.patch('/{user_id}', response_model=dict)
async def update_user(user_id:UUID, body:UserUpdate, db:AsyncSession=Depends(get_db), admin:User=Depends(require_roles(Role.ADMIN.value))):
    user=await db.get(User,user_id)
    if not user: raise HTTPException(404,'User not found')
    if body.role is not None and body.role not in {r.value for r in Role}: raise HTTPException(400,'Invalid role')
    if user.id==admin.id and body.is_active is False: raise HTTPException(400,'Administrator cannot deactivate the current account')
    would_be_admin = body.role == Role.ADMIN.value if body.role is not None else user.role == Role.ADMIN.value
    would_be_active = body.is_active if body.is_active is not None else user.is_active
    if user.role == Role.ADMIN.value and user.is_active and (not would_be_admin or not would_be_active):
        active_admins = int(await db.scalar(select(func.count(User.id)).where(User.role == Role.ADMIN.value, User.is_active.is_(True))) or 0)
        if active_admins <= 1:
            raise HTTPException(409, 'Cannot remove the last active administrator')
    for field in ('full_name','role','is_active'):
        value=getattr(body,field)
        if value is not None: setattr(user,field,value)
    await record_audit(db, actor_user_id=admin.id, action='user.updated', resource_type='user', resource_id=user.id, metadata={'role':user.role,'is_active':user.is_active})
    await db.commit(); return {'id':str(user.id),'email':user.email,'full_name':user.full_name,'role':user.role,'is_active':user.is_active}
