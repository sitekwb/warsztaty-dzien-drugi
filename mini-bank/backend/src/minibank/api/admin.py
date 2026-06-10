"""Admin endpoints — audit log integrity verification."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import AuditLogEntry, User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.services.audit_service import GENESIS_HASH, _compute_row_hash

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit/verify")
def verify_audit_chain(
    _user: User = Depends(require_role("admin", "supervisor")),
    db: Session = Depends(get_db),
):
    """Walk audit_log in id order, recompute row_hash, report first break."""
    stmt = select(AuditLogEntry).order_by(AuditLogEntry.id)
    entries = list(db.execute(stmt).scalars().all())
    prev = GENESIS_HASH
    for e in entries:
        if e.prev_hash != prev:
            return {"ok": False, "entries": len(entries), "first_broken_id": e.id}
        recomputed = _compute_row_hash(
            prev, e.actor_user_id, e.action, e.target_type, e.target_id, e.payload
        )
        if e.row_hash != recomputed:
            return {"ok": False, "entries": len(entries), "first_broken_id": e.id}
        prev = e.row_hash
    return {"ok": True, "entries": len(entries), "first_broken_id": None}
