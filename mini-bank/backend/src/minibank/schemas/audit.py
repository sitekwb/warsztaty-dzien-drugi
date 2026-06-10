"""Audit log response schema (used by future v3 endpoints; v2 just writes)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ts: datetime
    actor_user_id: UUID
    action: str
    target_type: str | None
    target_id: str | None
    payload: dict | None
