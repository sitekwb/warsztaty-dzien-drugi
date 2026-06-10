"""Transfer service.

BUG-01 LIVES IN THIS MODULE (planted bug, retained on `main`):
the read-modify-write on Account.balance is not atomic at the SQL level —
two concurrent execute_transfer calls on the same source can both pass the
overdraft check and both commit, overdrawing the account. This is intentional
and demonstrated by tests/e2e/test_concurrent_api.py (Task 21).
"""

from __future__ import annotations

import time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from minibank.db.models import Account, Currency, Transaction, TransactionStatus
from minibank.services import category_service


class OverdraftError(Exception):
    """Raised when a transfer would breach the source account's overdraft floor."""


def _available(account: Account) -> Decimal:
    return account.balance + account.overdraft_limit


def execute_transfer(
    db: Session,
    *,
    initiator_id: UUID,
    source_account_id: UUID,
    dest_iban: str,
    amount: Decimal,
    currency: str,
    title: str | None,
    recipient_name: str,
    _race_delay: float = 0.01,
) -> Transaction:
    """Move funds from source to destination IBAN, persist Transaction.

    BUG-01: classic check-then-act. Two concurrent calls on the same source can
    both pass the available-funds check before either commits the debit.
    """
    if amount <= 0:
        raise ValueError("transfer amount must be positive")

    source = db.get(Account, source_account_id)
    if source is None:
        raise ValueError(f"source account {source_account_id} not found")
    if source.status != "open":
        raise OverdraftError("source account is not open")

    dest = db.execute(select(Account).where(Account.holder_iban == dest_iban)).scalar_one_or_none()

    # --- BUG-01 starts here: check-then-act, no lock ---
    if _available(source) < amount:
        raise OverdraftError(
            f"insufficient funds in {source_account_id}: available {_available(source)} < {amount}"
        )

    # The race window: yield so a second thread can read the same stale balance.
    time.sleep(_race_delay)

    # v3: dual-approval threshold check
    LARGE_PLN_THRESHOLD = Decimal("50000")
    LARGE_EXTERNAL_PLN_THRESHOLD = Decimal("10000")
    requires_dual = False
    if currency == "PLN":
        is_external = dest is None
        if amount >= LARGE_PLN_THRESHOLD or (is_external and amount >= LARGE_EXTERNAL_PLN_THRESHOLD):
            requires_dual = True

    # v3: AML threshold (amount_in_eur > 15000 -> requires_review)
    from minibank.config import get_settings
    s = get_settings()
    if currency == "PLN":
        amount_in_eur = amount / s.pln_per_eur
    elif currency == "EUR":
        amount_in_eur = amount
    else:
        amount_in_eur = amount  # USD treated 1:1 for v3 simplification
    AML_EUR_THRESHOLD = Decimal("15000")
    requires_review = amount_in_eur > AML_EUR_THRESHOLD

    # status priority: requires_review > requires_dual_approval > completed
    if requires_review:
        status_val = TransactionStatus.REQUIRES_REVIEW.value
        do_debit = False
    elif requires_dual:
        status_val = TransactionStatus.REQUIRES_DUAL_APPROVAL.value
        do_debit = False
    else:
        status_val = TransactionStatus.COMPLETED.value
        do_debit = True

    if do_debit:
        source.balance -= amount
        if dest is not None:
            if dest.status != "open":
                raise OverdraftError("destination account is not open")
            dest.balance += amount
    # --- BUG-01 ends here ---

    trx = Transaction(
        source_account_id=source.id,
        dest_account_id=dest.id if dest else None,
        dest_iban=dest_iban,
        amount=amount,
        currency=Currency(currency),
        title=title,
        status=status_val,
        requires_dual_approval=requires_dual,
        initiated_by_user_id=initiator_id,
        recipient_name=recipient_name,
        category=category_service.categorize(title),
    )
    db.add(trx)
    db.commit()
    db.refresh(trx)
    return trx
