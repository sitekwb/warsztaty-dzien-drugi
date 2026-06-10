"""Customer-facing account endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from minibank.db.models import TransactionCategory, User
from minibank.db.session import get_db
from minibank.deps import require_role
from minibank.schemas.account import AccountResponse, TransactionResponse
from minibank.schemas.summary import AccountSummary
from minibank.services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _remap_incoming_category(tx, account_id: UUID) -> str:
    """Dla transakcji przychodzących na to konto, category w response = WPLYWY."""
    if tx.dest_account_id == account_id:
        return TransactionCategory.WPLYWY.value
    raw = tx.category
    return raw.value if hasattr(raw, "value") else raw


@router.get("", response_model=list[AccountResponse])
def list_my_accounts(
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    return account_service.list_customer_accounts(db, user.id)


@router.get("/{account_id}/transactions", response_model=list[TransactionResponse])
def list_my_transactions(
    account_id: UUID,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    acc = account_service.get_account(db, account_id)
    if acc is None or acc.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    rows = account_service.list_account_transactions_bidirectional(
        db, account_id, limit=limit, offset=offset
    )
    return [
        TransactionResponse(
            id=tx.id,
            source_account_id=tx.source_account_id,
            dest_account_id=tx.dest_account_id,
            dest_iban=tx.dest_iban,
            amount=tx.amount,
            currency=tx.currency.value if hasattr(tx.currency, "value") else tx.currency,
            title=tx.title,
            status=tx.status,
            created_at=tx.created_at,
            category=_remap_incoming_category(tx, account_id),
        )
        for tx in rows
    ]


@router.get("/{account_id}/summary", response_model=AccountSummary)
def get_account_summary(
    account_id: UUID,
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    acc = account_service.get_account(db, account_id)
    if acc is None or acc.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    now = datetime.now(timezone.utc)
    effective_month = month or f"{now.year:04d}-{now.month:02d}"
    return account_service.compute_summary(db, account_id, effective_month)
