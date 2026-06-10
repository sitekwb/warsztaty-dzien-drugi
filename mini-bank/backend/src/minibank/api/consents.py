"""Consent endpoints — agent requests, customer approves/rejects."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from minibank.db.models import ConsentScope, User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.services import consent_service

router = APIRouter(prefix="/consents", tags=["consents"])


class CreateConsentRequest(BaseModel):
    customer_id: UUID
    scope: ConsentScope = ConsentScope.READ
    ttl_minutes: int = Field(ge=5, le=1440, default=60)


@router.post("", status_code=status.HTTP_201_CREATED)
def request_consent(
    payload: CreateConsentRequest,
    user: User = Depends(require_role("agent", "supervisor")),
    db: Session = Depends(get_db),
):
    c = consent_service.request_consent(
        db, agent_user_id=user.id, customer_user_id=payload.customer_id,
        scope=payload.scope, ttl_minutes=payload.ttl_minutes,
    )
    db.commit(); db.refresh(c)
    return {"id": str(c.id), "status": c.status.value, "expires_at": c.expires_at.isoformat()}


@router.get("/pending")
def list_pending(
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    rows = consent_service.list_pending_for_customer(db, customer_user_id=user.id)
    return [
        {"id": str(r.id), "agent_user_id": str(r.agent_user_id),
         "scope": r.scope.value, "expires_at": r.expires_at.isoformat()}
        for r in rows
    ]


@router.post("/{consent_id}/approve")
def approve(
    consent_id: UUID,
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    c = consent_service.decide(db, consent_id=consent_id,
                               customer_user_id=user.id, approve=True)
    if c is None:
        raise HTTPException(404, "consent not found")
    db.commit()
    return {"ok": True}


@router.post("/{consent_id}/reject")
def reject(
    consent_id: UUID,
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    c = consent_service.decide(db, consent_id=consent_id,
                               customer_user_id=user.id, approve=False)
    if c is None:
        raise HTTPException(404, "consent not found")
    db.commit()
    return {"ok": True}
