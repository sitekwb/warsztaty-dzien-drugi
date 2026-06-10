"""JIT access grant request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateGrantRequest(BaseModel):
    customer_id: UUID
    ticket_id: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=1, max_length=2000)
    ttl_minutes: int = Field(ge=5, le=240, default=30)


class GrantResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    agent_user_id: UUID
    customer_user_id: UUID
    ticket_id: str
    reason: str
    granted_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
