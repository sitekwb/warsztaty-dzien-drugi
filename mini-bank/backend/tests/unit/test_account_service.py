"""Tests for account_service: list customer accounts, list transactions, PESEL masking."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Account, Currency, Role, User
from minibank.services import account_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


def _make_user_with_accounts(db, n_accounts: int) -> User:
    u = User(email="c@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="X", pesel="75102612345")
    db.add(u)
    db.flush()
    for i in range(n_accounts):
        db.add(Account(
            owner_user_id=u.id,
            holder_iban=f"PL12 1140 2004 0000 3000 0000 000{i}",
            balance=Decimal(f"{1000 + i * 500}"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        ))
    db.commit()
    return u


def test_list_customer_accounts(db):
    u = _make_user_with_accounts(db, 2)
    accs = account_service.list_customer_accounts(db, u.id)
    assert len(accs) == 2
    assert all(a.owner_user_id == u.id for a in accs)


def test_list_customer_accounts_empty(db):
    u = _make_user_with_accounts(db, 0)
    accs = account_service.list_customer_accounts(db, u.id)
    assert accs == []


def test_mask_pesel_pl_format():
    # Polish standard: show 2 leading + 3 trailing digits, mask middle.
    assert account_service.mask_pesel("75102612345") == "75******345"


def test_mask_pesel_none():
    assert account_service.mask_pesel(None) is None
