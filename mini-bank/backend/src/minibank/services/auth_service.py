"""Authentication service: bcrypt password hashing, JWT token encode/decode, user lookup.

JWT lives in HttpOnly cookie (set by api/auth.py), not LocalStorage.
Token TTL configured via settings.jwt_ttl_minutes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.config import get_settings
from minibank.db.models import User


def hash_password(plain: str) -> str:
    """Bcrypt-hash a plaintext password. Cost factor 12 (default)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time check of plaintext against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def encode_jwt(user_id: str, role: str) -> str:
    """Build a signed JWT carrying user_id (sub) and role."""
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=s.jwt_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    """Verify JWT signature + expiry; return claims dict. Raises jwt.PyJWTError on failure."""
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Look up user by email + verify password. Returns User on success, None on any failure."""
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.flush()
    return user
