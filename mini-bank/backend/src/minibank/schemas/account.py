"""Account schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AccountResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    holder_iban: str
    balance: Decimal
    currency: str
    status: str
    overdraft_limit: Decimal
    opened_on: date
    closed_on: date | None


class TransactionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    source_account_id: UUID
    dest_account_id: UUID | None
    dest_iban: str | None
    amount: Decimal
    currency: str
    title: str | None
    status: str
    created_at: datetime
    category: str
