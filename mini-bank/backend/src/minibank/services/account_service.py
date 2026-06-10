"""Account-related queries and presentation helpers.

PESEL masking lives here because it's a presentation concern — the DB stores the
plaintext value, and we mask at the API boundary based on viewer role.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from minibank.db.models import Account, Transaction, TransactionCategory, TransactionStatus


def list_customer_accounts(db: Session, customer_id: UUID) -> list[Account]:
    """Return all accounts owned by the given customer."""
    stmt = select(Account).where(Account.owner_user_id == customer_id).order_by(Account.created_at)
    return list(db.execute(stmt).scalars().all())


def get_account(db: Session, account_id: UUID) -> Account | None:
    """Fetch an account by id or return None."""
    return db.get(Account, account_id)


def list_account_transactions(
    db: Session, account_id: UUID, limit: int = 50, offset: int = 0
) -> list[Transaction]:
    """Return transactions where this account is the source, newest first."""
    stmt = (
        select(Transaction)
        .where(Transaction.source_account_id == account_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def mask_pesel(pesel: str | None) -> str | None:
    """Polish bank convention: keep 2 leading + 3 trailing digits, mask the middle 6.

    Example: '75102612345' -> '75******345'. Returns None for missing PESEL.
    """
    if pesel is None:
        return None
    if len(pesel) != 11:
        return pesel
    return f"{pesel[:2]}{'*' * 6}{pesel[-3:]}"


def _month_bounds(month: str) -> tuple[datetime, datetime]:
    """Zwraca [start, end) miesiąca w UTC. Format: 'YYYY-MM'."""
    year, mon = month.split("-")
    start = datetime(int(year), int(mon), 1, tzinfo=timezone.utc)
    if int(mon) == 12:
        end = datetime(int(year) + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(int(year), int(mon) + 1, 1, tzinfo=timezone.utc)
    return start, end


def compute_summary(db: Session, account_id: UUID, month: str) -> dict:
    """Wpływy, wydatki, saldo MTD + breakdown wydatków per kategoria.

    `month` w formacie 'YYYY-MM'. Liczy wyłącznie transakcje ze statusem COMPLETED.
    `by_category` pomija WPLYWY i PRZELEW_WLASNY.
    """
    start, end = _month_bounds(month)

    inflow_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.dest_account_id == account_id,
        Transaction.status == TransactionStatus.COMPLETED.value,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )
    outflow_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.source_account_id == account_id,
        Transaction.status == TransactionStatus.COMPLETED.value,
        Transaction.created_at >= start,
        Transaction.created_at < end,
    )

    inflow = Decimal(str(db.execute(inflow_q).scalar() or 0))
    outflow = Decimal(str(db.execute(outflow_q).scalar() or 0))

    cat_q = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.source_account_id == account_id,
            Transaction.status == TransactionStatus.COMPLETED.value,
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.category.notin_([
                TransactionCategory.WPLYWY,
                TransactionCategory.PRZELEW_WLASNY,
            ]),
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    by_category = [
        {
            "category": row.category.value if hasattr(row.category, "value") else row.category,
            "total": Decimal(str(row.total)),
        }
        for row in db.execute(cat_q).all()
    ]

    return {
        "month": month,
        "inflow": inflow,
        "outflow": outflow,
        "mtd_balance": inflow - outflow,
        "by_category": by_category,
    }


def list_account_transactions_bidirectional(
    db: Session, account_id: UUID, limit: int = 50, offset: int = 0
) -> list[Transaction]:
    """Transakcje gdzie konto jest źródłem LUB celem, najnowsze pierwsze."""
    stmt = (
        select(Transaction)
        .where(or_(Transaction.source_account_id == account_id,
                   Transaction.dest_account_id == account_id))
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())
