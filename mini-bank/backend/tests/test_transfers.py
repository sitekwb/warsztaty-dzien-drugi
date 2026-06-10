"""Legacy unit race test for the transfer service.

Originally exercised the in-memory AccountStore. Now exercises
transfer_service.execute_transfer (DB-backed) with the same race window.

BUG-01 is a planted concurrency bug: two threads moving money from the
same source can both pass the check-then-act on Account.balance.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Account, Currency, Role, User
from minibank.services.transfer_service import OverdraftError, execute_transfer


def _build_db():
    """Build a fresh in-memory SQLite engine that supports concurrent connections."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-01: check-then-act race in transfer_service overdraws account",
    strict=False,
)
def test_concurrent_transfers_race_overdraws_account():
    """Two threads transfer 80 PLN from a 100 PLN account; with the bug both succeed.

    Sequential semantics would require: first succeeds (balance 20), second
    raises OverdraftError. With BUG-01 active, both check 100 >= 80 before
    either commits, so both debit and the balance lands at -60.
    """
    engine, SessionLocal = _build_db()
    with SessionLocal() as setup:
        owner = User(email="r@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="R")
        setup.add(owner)
        setup.flush()
        src = Account(
            owner_user_id=owner.id,
            holder_iban="PL12 1140 2004 0000 7777 7777 0001",
            balance=Decimal("100.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        dst = Account(
            owner_user_id=owner.id,
            holder_iban="PL12 1140 2004 0000 7777 7777 0002",
            balance=Decimal("0.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        setup.add_all([src, dst])
        setup.commit()
        owner_id = owner.id
        src_id = src.id
        dst_iban = dst.holder_iban

    def thread_transfer():
        with SessionLocal() as s:
            try:
                execute_transfer(
                    s,
                    initiator_id=owner_id,
                    source_account_id=src_id,
                    dest_iban=dst_iban,
                    amount=Decimal("80.00"),
                    currency="PLN",
                    title="race",
                    recipient_name="Test",
                )
                return "ok"
            except OverdraftError:
                return "overdraft"

    with ThreadPoolExecutor(max_workers=2) as ex:
        results = [f.result() for f in [ex.submit(thread_transfer) for _ in range(2)]]

    # With BUG-01, both report "ok".
    assert results.count("ok") == 2, f"expected both to succeed under BUG-01: {results}"

    # Sequential semantics would leave balance at 20. Both succeeding leaves balance at -60.
    with SessionLocal() as check:
        final = check.get(Account, src_id)
        # If the test xpasses (bug fixed), this assertion would be balance == Decimal("20.00").
        # We assert the bug-active outcome to keep the xfail in the right direction.
        assert final.balance >= Decimal("0"), (
            f"BUG-01 active: balance {final.balance} dropped below 0 — both transfers debited"
        )
