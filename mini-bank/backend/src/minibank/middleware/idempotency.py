"""Idempotency cache (Stripe pattern).

BUG-09 PLANTED: `cache_lookup` returns the stored response whenever the key
matches, IGNORING request_hash mismatch. Correct spec: same key + different
request body must surface as 409 Conflict.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from sqlalchemy.orm import Session

from minibank.db.models import IdempotencyKey


def compute_request_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cache_lookup(db: Session, *, key: UUID, request_hash: str) -> tuple[dict | None, int | None]:
    """Return (response_body, status_code) on hit, (None, None) on miss.

    BUG-09: when there is a row for `key`, we return its response REGARDLESS
    of whether request_hash matches. Correct: mismatch -> (None, 409).
    """
    row = db.get(IdempotencyKey, key)
    if row is None:
        return None, None
    # BUG-09: should be: if row.request_hash != request_hash: return None, 409
    return row.response_body, row.status_code


def cache_store(db: Session, *, key: UUID, user_id: UUID, request_hash: str,
                response_body: dict, status_code: int) -> IdempotencyKey:
    row = IdempotencyKey(
        key=key, user_id=user_id, request_hash=request_hash,
        response_body=response_body, status_code=status_code,
    )
    db.add(row)
    db.flush()
    return row
