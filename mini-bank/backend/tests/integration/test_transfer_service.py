"""Integration tests for transfer_service against a real SQLite DB.

BUG-01 (race condition) lives in the service and is invoked from
transfer_service.execute_transfer. The race is *not* covered by these
single-thread tests — it surfaces in tests/e2e/test_concurrent_api.py (Task 21).
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Account, Currency, Role, User
from minibank.services import transfer_service
from minibank.services.transfer_service import OverdraftError


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


@pytest.fixture
def src_and_dest(db):
    u1 = User(email="a@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="A")
    u2 = User(email="b@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="B")
    db.add_all([u1, u2])
    db.flush()
    src = Account(
        owner_user_id=u1.id,
        holder_iban="PL12 1140 2004 0000 3000 0000 0001",
        balance=Decimal("1000.00"),
        currency=Currency.PLN,
        opened_on=date(2024, 1, 1),
    )
    dst = Account(
        owner_user_id=u2.id,
        holder_iban="PL12 1140 2004 0000 3000 0000 0002",
        balance=Decimal("500.00"),
        currency=Currency.PLN,
        opened_on=date(2024, 1, 1),
    )
    db.add_all([src, dst])
    db.commit()
    return u1, src, dst


def test_transfer_moves_funds(db, src_and_dest):
    user, src, dst = src_and_dest
    trx = transfer_service.execute_transfer(
        db,
        initiator_id=user.id,
        source_account_id=src.id,
        dest_iban=dst.holder_iban,
        amount=Decimal("200.00"),
        currency="PLN",
        title="Test",
        recipient_name="Test",
    )
    db.refresh(src)
    db.refresh(dst)
    assert src.balance == Decimal("800.00")
    assert dst.balance == Decimal("700.00")
    assert trx.status == "completed"
    assert trx.dest_account_id == dst.id


def test_transfer_external_iban_no_dest_account(db, src_and_dest):
    user, src, _ = src_and_dest
    trx = transfer_service.execute_transfer(
        db,
        initiator_id=user.id,
        source_account_id=src.id,
        dest_iban="PL12 1140 2004 9999 9999 9999 9999",
        amount=Decimal("100.00"),
        currency="PLN",
        title="External",
        recipient_name="Test",
    )
    db.refresh(src)
    assert src.balance == Decimal("900.00")
    assert trx.dest_account_id is None
    assert trx.status == "completed"


def test_transfer_insufficient_funds_raises(db, src_and_dest):
    user, src, dst = src_and_dest
    with pytest.raises(OverdraftError):
        transfer_service.execute_transfer(
            db,
            initiator_id=user.id,
            source_account_id=src.id,
            dest_iban=dst.holder_iban,
            amount=Decimal("99999.00"),
            currency="PLN",
            title="Too much",
            recipient_name="Test",
        )


def test_transfer_negative_amount_raises(db, src_and_dest):
    user, src, dst = src_and_dest
    with pytest.raises(ValueError):
        transfer_service.execute_transfer(
            db,
            initiator_id=user.id,
            source_account_id=src.id,
            dest_iban=dst.holder_iban,
            amount=Decimal("-1.00"),
            currency="PLN",
            title="bad",
            recipient_name="Test",
        )
