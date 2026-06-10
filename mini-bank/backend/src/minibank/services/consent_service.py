"""Consent service: agent requests, customer approves/rejects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import Consent, ConsentScope, ConsentStatus


def request_consent(
    db: Session, *, agent_user_id: UUID, customer_user_id: UUID,
    scope: ConsentScope, ttl_minutes: int,
) -> Consent:
    now = datetime.now(timezone.utc)
    c = Consent(agent_user_id=agent_user_id, customer_user_id=customer_user_id,
                scope=scope, granted_at=now,
                expires_at=now + timedelta(minutes=ttl_minutes),
                status=ConsentStatus.PENDING)
    db.add(c); db.flush(); db.refresh(c)
    return c


def list_pending_for_customer(db: Session, *, customer_user_id: UUID) -> list[Consent]:
    stmt = (select(Consent)
            .where(Consent.customer_user_id == customer_user_id)
            .where(Consent.status == ConsentStatus.PENDING)
            .order_by(Consent.granted_at.desc()))
    return list(db.execute(stmt).scalars().all())


def decide(db: Session, *, consent_id: UUID, customer_user_id: UUID,
           approve: bool) -> Consent | None:
    c = db.get(Consent, consent_id)
    if c is None or c.customer_user_id != customer_user_id:
        return None
    c.status = ConsentStatus.APPROVED if approve else ConsentStatus.REJECTED
    c.decided_at = datetime.now(timezone.utc)
    db.flush()
    return c
