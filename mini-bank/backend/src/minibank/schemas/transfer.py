"""Transfer request schema."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    source_account_id: UUID
    dest_iban: str = Field(min_length=15, max_length=40)
    recipient_name: str = Field(min_length=3, max_length=140)
    amount: Decimal = Field(gt=Decimal("0"))
    currency: str = Field(pattern=r"^(PLN|EUR|USD)$")
    title: str | None = Field(default=None, max_length=140)


class TransferResponse(BaseModel):
    transaction_id: UUID
    status: str


class TransferInitiateResponse(BaseModel):
    sca_challenge_id: str
    expires_at: str


class ScaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
