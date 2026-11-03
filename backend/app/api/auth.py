from datetime import datetime, timedelta, timezone
import hashlib, secrets
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth import authenticate, issue_tokens, rotate_refresh_token, create_user
from app.api.deps import get_current_user, require_roles
from app.models.models import User, Role, PasswordResetToken, RefreshSession
from app.schemas.common import TokenPair, UserOut
from app.core.security import hash_password
from app.core.config import settings
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])
class LoginRequest(BaseModel): email: str = Field(min_length=3, max_length=320); password: str = Field(min_length=1, max_length=256)
class RefreshRequest(BaseModel): refresh_token: str | None = None
class UserCreate(BaseModel):
    email: EmailStr; full_name: str = Field(min_length=1,max_length=200); password: str = Field(min_length=12,max_length=256); role: str
class PasswordResetRequest(BaseModel): email: EmailStr
class PasswordResetConfirm(BaseModel): token: str; new_password: str = Field(min_length=12,max_length=256)

# Browser sessions keep the refresh token in an HttpOnly cookie scoped to the auth routes, so
# page scripts never see it; the short-lived access token lives only in frontend memory.
# The body field remains for non-browser API clients.
REFRESH_COOKIE = 'dps_refresh'
REFRESH_COOKIE_PATH = '/api/v1/auth'


def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(REFRESH_COOKIE, token, max_age=settings.refresh_token_days * 86400, httponly=True,
                        secure=settings.environment == 'production', samesite='strict', path=REFRESH_COOKIE_PATH)


@router.post('/login', response_model=TokenPair)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, body.email, body.password)
    if not user: raise HTTPException(status_code=401, detail='Invalid credentials')
    access, refresh = await issue_tokens(db, user); await record_audit(db, actor_user_id=user.id, action='auth.login', resource_type='user', resource_id=user.id, commit=True)
    _set_refresh_cookie(response, refresh)
    return TokenPair(access_token=access, refresh_token=refresh)

@router.post('/refresh', response_model=TokenPair)
async def refresh(response: Response, body: RefreshRequest | None = None, db: AsyncSession = Depends(get_db), dps_refresh: str | None = Cookie(default=None)):
    raw = (body.refresh_token if body else None) or dps_refresh
    if not raw: raise HTTPException(status_code=401, detail='Invalid refresh token')
    try: access, token = await rotate_refresh_token(db, raw)
    except Exception: raise HTTPException(status_code=401, detail='Invalid refresh token') from None
    _set_refresh_cookie(response, token)
    return TokenPair(access_token=access, refresh_token=token)

@router.post('/logout')
async def logout(response: Response, body: RefreshRequest | None = None, db: AsyncSession = Depends(get_db), dps_refresh: str | None = Cookie(default=None)):
    """Revoke the presented refresh session. Works with an expired access token so sign-out always succeeds."""
    from app.core.security import decode_token
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    raw = (body.refresh_token if body else None) or dps_refresh
    try: payload = decode_token(raw or '', 'refresh')
    except Exception: return {'message':'Logged out'}
    session = await db.scalar(select(RefreshSession).where(RefreshSession.token_jti == payload.get('jti')))
    if session and str(session.user_id) == str(payload.get('sub')):
        session.revoked_at = datetime.now(timezone.utc)
        await record_audit(db, actor_user_id=session.user_id, action='auth.logout', resource_type='user', resource_id=session.user_id)
        await db.commit()
    return {'message':'Logged out'}

@router.post('/password-reset/request')
async def request_reset(body: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email.lower().strip()))
    token = secrets.token_urlsafe(48)
    if user and user.is_active:
        now = datetime.now(timezone.utc)
        await db.execute(PasswordResetToken.__table__.update().where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).values(used_at=now))
        raw_hash = hashlib.sha256(token.encode()).hexdigest()
        db.add(PasswordResetToken(user_id=user.id, token_hash=raw_hash, expires_at=now+timedelta(minutes=30)))
        await record_audit(db, actor_user_id=user.id, action='auth.password_reset_requested', resource_type='user', resource_id=user.id)
        await db.commit()
        result={'message':'If the account exists, a password reset has been issued.'}
        if settings.expose_demo_reset_token and settings.environment != 'production': result['demo_token']=token
        return result
    await db.commit(); return {'message':'If the account exists, a password reset has been issued.'}

@router.post('/password-reset/confirm')
async def confirm_reset(body: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    row = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    if not row or row.used_at or row.expires_at <= now: raise HTTPException(status_code=400, detail='Invalid or expired reset token')
    user = await db.get(User, row.user_id)
    if not user or not user.is_active: raise HTTPException(status_code=400, detail='Invalid or expired reset token')
    user.password_hash = hash_password(body.new_password); row.used_at = now
    await db.execute(RefreshSession.__table__.update().where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None)).values(revoked_at=now))
    await record_audit(db, actor_user_id=user.id, action='auth.password_reset_completed', resource_type='user', resource_id=user.id)
    await db.commit(); return {'message':'Password reset completed'}

@router.get('/me', response_model=UserOut)
async def me(user: User = Depends(get_current_user)): return user

@router.post('/users', response_model=UserOut)
async def create_staff(body: UserCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles(Role.ADMIN.value))):
    try: user = await create_user(db, body.email, body.full_name, body.password, body.role)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
    await record_audit(db, actor_user_id=admin.id, action='user.created', resource_type='user', resource_id=user.id); await db.commit(); await db.refresh(user); return user
