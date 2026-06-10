"""Account finance summary — KPI + by-category breakdown."""
from decimal import Decimal

from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class AccountSummary(BaseModel):
    month: str
    inflow: Decimal
    outflow: Decimal
    mtd_balance: Decimal
    by_category: list[CategoryTotal]
