"""Concurrent transfer logic for the mini-bank.

PLANTED BUG-01 (race condition)
-------------------------------
``transfer`` performs a classic check-then-act on the source balance with no
synchronisation. Two threads moving money out of the same account can both read
the same starting balance, both pass the overdraft check, and both commit their
debit -- overdrawing the account past its limit.

The bug is real but timing-dependent. The deliberate ``time.sleep`` between the
read and the write widens the race window so the failing test reproduces it
reliably during the workshop. Removing the sleep does not fix the bug; it only
makes it harder to observe.

Block 1 attendees diagnose this in Exercise 2 (plan mode) and the fix lands in
the solutions branch (guard the read-modify-write with a per-source lock or an
atomic compare-and-debit).
"""

from __future__ import annotations

import time
from decimal import Decimal

from .._account_store import AccountStore


class OverdraftError(Exception):
    """Raised when a transfer would breach the source account's overdraft floor."""


def transfer(
    store: AccountStore,
    source_id: str,
    dest_id: str,
    amount: Decimal,
    *,
    _race_delay: float = 0.01,
) -> None:
    """Move ``amount`` from ``source_id`` to ``dest_id``.

    Racy by design (BUG-01): the available-funds check and the debit are not
    atomic, so concurrent callers can both pass the check before either writes.
    """
    if amount <= 0:
        raise ValueError("transfer amount must be positive")

    source = store.get(source_id)
    dest = store.get(dest_id)

    if source.status != "open" or dest.status != "open":
        raise OverdraftError("both accounts must be open")

    # --- BUG-01 starts here: check-then-act with no lock -------------------
    # Read the available balance...
    if source.available() < amount:
        raise OverdraftError(
            f"insufficient funds in {source_id}: "
            f"available {source.available()} < {amount}"
        )

    # ...yield the CPU so a second thread can pass the same check on the same
    # stale balance before we commit our debit. This is the race window.
    time.sleep(_race_delay)

    # ...then act on a balance that may already be stale.
    source.balance -= amount
    dest.balance += amount
    # --- BUG-01 ends here --------------------------------------------------
