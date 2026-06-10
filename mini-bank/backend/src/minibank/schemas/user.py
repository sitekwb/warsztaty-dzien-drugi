"""User response schemas — with role-aware PESEL masking."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    """User as seen by themselves (full PESEL)."""

    model_config = {"from_attributes": True}

    id: UUID
    email: EmailStr
    role: str
    full_name: str
    pesel: str | None
    citizenship: str
    created_at: datetime


class UserMasked(BaseModel):
    """User as seen by an agent (masked PESEL)."""

    model_config = {"from_attributes": True}

    id: UUID
    email: EmailStr
    role: str
    full_name: str
    pesel_masked: str | None
    citizenship: str
