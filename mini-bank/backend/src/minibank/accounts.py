"""Account model and storage. Stub authored in Phase A; Block 1 subagent extends."""

from decimal import Decimal

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    holder_iban: str
    balance: Decimal
    status: str = "open"  # open | closed
    # Overdraft floor: how far below zero this account may legally go.
    # Default 0 => no overdraft permitted. Transfers must respect this limit.
    overdraft_limit: Decimal = Decimal("0")

    def available(self) -> Decimal:
        """Funds that may be withdrawn without breaching the overdraft floor."""
        return self.balance + self.overdraft_limit
