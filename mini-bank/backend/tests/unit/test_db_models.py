"""Tests for SQLAlchemy ORM models — schema shape, roles, defaults."""

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Account, Currency, Role, Transaction, User


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


def test_user_basic_roles(session):
    user = User(
        email="customer1@minibank.pl",
        password_hash="$2b$12$dummy",
        role=Role.CUSTOMER,
        full_name="Jan Kowalski",
        pesel="75102612345",
        citizenship="PL",
    )
    session.add(user)
    session.commit()
    assert isinstance(user.id, UUID)
    assert user.role == Role.CUSTOMER


def test_account_balance_is_decimal(session):
    user = User(email="c2@minibank.pl", password_hash="x", role=Role.CUSTOMER, full_name="Anna Nowak")
    session.add(user)
    session.flush()
    acc = Account(
        owner_user_id=user.id,
        holder_iban="PL12 1140 2004 0000 3000 0000 0001",
        balance=Decimal("1234.56"),
        currency=Currency.PLN,
        opened_on="2024-01-01",
    )
    session.add(acc)
    session.commit()
    assert acc.balance == Decimal("1234.56")
    assert acc.status == "open"
    assert acc.overdraft_limit == Decimal("0")


def test_transaction_status_enum(session):
    user = User(email="c3@minibank.pl", password_hash="x", role=Role.CUSTOMER, full_name="Tomasz K")
    session.add(user)
    session.flush()
    acc = Account(
        owner_user_id=user.id,
        holder_iban="PL12 1140 2004 0000 3000 0000 0002",
        balance=Decimal("500.00"),
        currency=Currency.PLN,
        opened_on="2024-01-01",
    )
    session.add(acc)
    session.flush()
    trx = Transaction(
        source_account_id=acc.id,
        dest_iban="PL12 1140 2004 0000 3000 0000 0099",
        amount=Decimal("100.00"),
        currency=Currency.PLN,
        title="Test",
        status="completed",
        initiated_by_user_id=user.id,
        recipient_name="Test odbiorca",
    )
    session.add(trx)
    session.commit()
    assert trx.status == "completed"
