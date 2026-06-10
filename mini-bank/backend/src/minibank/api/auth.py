"""Authentication endpoints: login (sets HttpOnly cookie), logout (clears), me (current user)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.config import get_settings
from minibank.db.models import JitAccessGrant, User
from minibank.db.session import get_db
from minibank.deps import COOKIE_NAME, get_current_user
from minibank.schemas.auth import LoginRequest, LoginResponse
from minibank.services.auth_service import authenticate, encode_jwt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    db.commit()
    token = encode_jwt(user_id=str(user.id), role=user.role.value)
    s = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=s.environment != "dev",
        samesite="lax",
        max_age=s.jwt_ttl_minutes * 60,
    )
    return LoginResponse(user_id=str(user.id), role=user.role.value, full_name=user.full_name)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=LoginResponse)
def me(user: User = Depends(get_current_user)):
    return LoginResponse(user_id=str(user.id), role=user.role.value, full_name=user.full_name)


@router.get("/active-agent-access")
def my_active_agent_access(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return grants that other agents currently hold on the calling customer.

    Note: this DOES check expires_at (customer-facing endpoint, so we want
    correct info there). The BUG-06 expires_at miss is in the
    `is_active_grant` gate used by agent endpoints — that's where the
    teaching moment lives.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(JitAccessGrant)
        .where(JitAccessGrant.customer_user_id == user.id)
        .where(JitAccessGrant.revoked_at.is_(None))
        .where(JitAccessGrant.expires_at > now)
    )
    grants = list(db.execute(stmt).scalars().all())
    return [
        {
            "id": str(g.id),
            "ticket_id": g.ticket_id,
            "expires_at": g.expires_at.isoformat(),
            "agent_user_id": str(g.agent_user_id),
        }
        for g in grants
    ]


class StepUpRequest(BaseModel):
    code: str


@router.post("/step-up")
def step_up(
    _body: StepUpRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """v3 simplified: accept any code. Real implementation would verify TOTP."""
    user.last_step_up_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}
