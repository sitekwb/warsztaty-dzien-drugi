"""PSD2 SCA dynamic-linking service.

BUG-08 PLANTED: verify() ignores request_amount / request_dest_iban — only
checks the code and the expires_at + used_at. Correct PSD2 dynamic linking
requires the code to be valid only for the (amount, iban) pair the user saw.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import bcrypt
from sqlalchemy.orm import Session

from minibank.db.models import ScaChallenge


SCA_TTL_SECONDS = 60


class ScaError(Exception):
    """Raised when SCA verification fails."""


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_challenge(
    db: Session,
    *,
    user_id: UUID,
    amount: Decimal,
    dest_iban: str,
    pending_payload: dict,
) -> tuple[ScaChallenge, str]:
    code = _generate_code()
    code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    now = datetime.now(timezone.utc)
    ch = ScaChallenge(
        user_id=user_id, code_hash=code_hash,
        linked_amount=amount, linked_dest_iban=dest_iban,
        pending_payload=pending_payload,
        created_at=now, expires_at=now + timedelta(seconds=SCA_TTL_SECONDS),
    )
    db.add(ch); db.flush(); db.refresh(ch)
    return ch, code


def verify(
    db: Session,
    *,
    challenge_id: UUID,
    code: str,
    request_amount: Decimal,
    request_dest_iban: str,
) -> dict:
    """Return pending_payload on success. Raise ScaError on any failure.

    BUG-08: the request_amount / request_dest_iban arguments are ACCEPTED but
    NOT compared with the linked_amount / linked_dest_iban stored on the
    challenge. Solutions branch adds those two checks.
    """
    ch = db.get(ScaChallenge, challenge_id)
    if ch is None:
        raise ScaError("challenge not found")
    if ch.used_at is not None:
        raise ScaError("challenge already used")
    now = datetime.now(timezone.utc)
    expires_at = ch.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise ScaError("challenge expired")
    if not bcrypt.checkpw(code.encode("utf-8"), ch.code_hash.encode("utf-8")):
        raise ScaError("invalid code")
    # BUG-08: missing dynamic-linking check:
    #   if request_amount != ch.linked_amount or request_dest_iban != ch.linked_dest_iban:
    #       raise ScaError("dynamic-linking mismatch")
    ch.used_at = now
    db.flush()
    return ch.pending_payload
