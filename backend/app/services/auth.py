from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.models import LoginAttempt, RefreshSession, Role, User

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        db.add(LoginAttempt(email=email.lower().strip(), success=False))
        await db.commit()
        return None
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return None
    ok = verify_password(password, user.password_hash)
    db.add(LoginAttempt(email=user.email, success=ok))
    if ok:
        user.failed_login_count = 0
        user.locked_until = None
    else:
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    await db.commit()
    return user if ok else None

async def issue_tokens(db: AsyncSession, user: User):
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    payload = decode_token(refresh, "refresh")
    expires = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.add(RefreshSession(user_id=user.id, token_jti=payload["jti"], expires_at=expires))
    await db.commit()
    return access, refresh

async def rotate_refresh_token(db: AsyncSession, token: str):
    payload = decode_token(token, "refresh")
    result = await db.execute(select(RefreshSession).where(RefreshSession.token_jti == payload["jti"]).with_for_update())
    session = result.scalar_one_or_none()
    if not session or session.revoked_at or session.expires_at <= datetime.now(timezone.utc):
        raise ValueError("Refresh session is invalid")
    session.revoked_at = datetime.now(timezone.utc)
    user = await db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise ValueError("User is inactive")
    access, refresh = await issue_tokens(db, user)
    return access, refresh

async def create_user(db: AsyncSession, email: str, full_name: str, password: str, role: str):
    existing = await db.scalar(select(User).where(User.email == email.lower().strip()))
    if existing:
        raise ValueError("Email already exists")
    if role not in {r.value for r in Role}:
        raise ValueError("Invalid role")
    user = User(email=email.lower().strip(), full_name=full_name, password_hash=hash_password(password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
