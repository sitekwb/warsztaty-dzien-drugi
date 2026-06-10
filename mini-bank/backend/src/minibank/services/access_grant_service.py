"""Break-glass / JIT access grant service.

`create_grant` — issue a time-bounded grant for an agent to access a customer.
`list_active_for_agent` — show this agent's currently-active grants.
`revoke_grant` — flip `revoked_at` (the agent withdrawing access early).
`is_active_grant` — used by `require_active_grant` middleware to gate
customer-data endpoints.

BUG-06 PLANTED: `is_active_grant` only checks that the grant exists, matches
the customer, and is not revoked. It does NOT compare `now < expires_at`.
Result: a grant issued for 30 minutes remains "active" indefinitely. The fix
(solutions branch) compares `datetime.now(timezone.utc) < grant.expires_at`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import JitAccessGrant


def create_grant(
    db: Session,
    *,
    agent_user_id: UUID,
    customer_id: UUID,
    ticket_id: str,
    reason: str,
    ttl_minutes: int,
) -> JitAccessGrant:
    """Create a new active grant. Caller commits the session."""
    now = datetime.now(timezone.utc)
    grant = JitAccessGrant(
        agent_user_id=agent_user_id,
        customer_user_id=customer_id,
        ticket_id=ticket_id,
        reason=reason,
        granted_at=now,
        expires_at=now + timedelta(minutes=ttl_minutes),
    )
    db.add(grant)
    db.flush()
    db.refresh(grant)
    return grant


def list_active_for_agent(db: Session, *, agent_user_id: UUID) -> list[JitAccessGrant]:
    """Return grants owned by this agent that are not revoked. Expired
    grants are NOT filtered out — caller may show them with a 'wygasł'
    label if they want.
    """
    stmt = (
        select(JitAccessGrant)
        .where(JitAccessGrant.agent_user_id == agent_user_id)
        .where(JitAccessGrant.revoked_at.is_(None))
        .order_by(JitAccessGrant.granted_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def revoke_grant(db: Session, *, grant_id: UUID, agent_user_id: UUID) -> JitAccessGrant | None:
    """Set revoked_at on a grant owned by this agent. Returns None if not found."""
    grant = db.get(JitAccessGrant, grant_id)
    if grant is None or grant.agent_user_id != agent_user_id:
        return None
    if grant.revoked_at is None:
        grant.revoked_at = datetime.now(timezone.utc)
    db.flush()
    return grant


def is_active_grant(db: Session, *, grant_id: UUID, customer_id: UUID) -> bool:
    """Decide whether this grant authorises the bearer to act on this customer.

    BUG-06: missing expires_at check. The correct implementation includes
    `and now < grant.expires_at`.
    """
    grant = db.get(JitAccessGrant, grant_id)
    if grant is None:
        return False
    if grant.customer_user_id != customer_id:
        return False
    if grant.revoked_at is not None:
        return False
    # BUG-06: should also check datetime.now(timezone.utc) < grant.expires_at
    return True
