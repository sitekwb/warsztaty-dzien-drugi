"""FastAPI dependency-injection helpers for auth and DB sessions."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from minibank.db.models import User
from minibank.db.session import get_db
from minibank.services.auth_service import decode_jwt

COOKIE_NAME = "access_token"


def get_current_user(
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT in the HttpOnly cookie to a User row, or 401."""
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    try:
        claims = decode_jwt(access_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    user_id_raw = claims.get("sub")
    if user_id_raw is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="malformed token")
    user = db.get(User, UUID(user_id_raw))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """Dependency factory: gate an endpoint to one of `allowed_roles`."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _checker
