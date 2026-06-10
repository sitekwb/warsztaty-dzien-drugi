"""DB-backed audit log writer with SHA-256 hash chain.

BUG-07 PLANTED (from v2): payload persisted verbatim — PESEL leaks.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import AuditLogEntry


GENESIS_HASH = "0" * 64


def _canonical_payload(payload: dict | None) -> str:
    if payload is None:
        return ""
    return json.dumps(payload, sort_keys=True, separators=(", ", ": "))


def _compute_row_hash(prev_hash: str, actor_user_id: UUID, action: str,
                      target_type: str | None, target_id: str | None,
                      payload: dict | None) -> str:
    parts = [
        prev_hash,
        str(actor_user_id),
        action,
        target_type or "",
        target_id or "",
        _canonical_payload(payload),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _last_row_hash(db: Session) -> str:
    stmt = select(AuditLogEntry.row_hash).order_by(AuditLogEntry.id.desc()).limit(1)
    last = db.execute(stmt).scalar_one_or_none()
    return last or GENESIS_HASH


def record(
    db: Session,
    *,
    actor_user_id: UUID,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict | None = None,
) -> AuditLogEntry:
    if actor_user_id is None:
        raise ValueError("audit entry requires a named actor")
    if not action:
        raise ValueError("audit entry requires an action")

    prev = _last_row_hash(db)
    row_hash = _compute_row_hash(prev, actor_user_id, action, target_type, target_id, payload)

    entry = AuditLogEntry(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
        prev_hash=prev,
        row_hash=row_hash,
    )
    db.add(entry)
    db.flush()
    db.refresh(entry)
    return entry
