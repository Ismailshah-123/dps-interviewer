from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from .config import settings

_password_hasher = PasswordHasher()
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return _password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False

def create_token(subject: UUID, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(subject), "type": token_type, "iat": now, "exp": now + expires_delta, "jti": str(UUID(bytes=__import__('os').urandom(16)))}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise ValueError("Invalid token type")
    return payload

def create_access_token(subject: UUID) -> str:
    return create_token(subject, "access", timedelta(minutes=settings.access_token_minutes))

def create_refresh_token(subject: UUID) -> str:
    return create_token(subject, "refresh", timedelta(days=settings.refresh_token_days))
