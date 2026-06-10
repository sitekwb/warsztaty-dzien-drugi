"""Tests for agent_service: list customers, search, get by id."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Role, User
from minibank.services import agent_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        for i in range(3):
            s.add(User(
                email=f"c{i}@x.pl",
                password_hash="x",
                role=Role.CUSTOMER,
                full_name=f"Customer {i}",
                pesel=f"7510261234{i}",
            ))
        s.add(User(email="agent@x.pl", password_hash="x", role=Role.AGENT, full_name="Agent A"))
        s.commit()
        yield s


def test_list_customers_returns_only_customers(db):
    customers = agent_service.list_customers(db)
    assert len(customers) == 3
    assert all(c.role == Role.CUSTOMER for c in customers)


def test_search_customers_by_name(db):
    found = agent_service.list_customers(db, search="Customer 1")
    assert len(found) == 1
    assert found[0].full_name == "Customer 1"


def test_search_customers_by_email(db):
    found = agent_service.list_customers(db, search="c2@x.pl")
    assert len(found) == 1


def test_get_customer_by_id(db):
    all_c = agent_service.list_customers(db)
    target_id = all_c[0].id
    c = agent_service.get_customer(db, target_id)
    assert c is not None
    assert c.id == target_id


def test_get_customer_not_a_customer(db):
    agent = db.query(User).filter(User.role == Role.AGENT).one()
    c = agent_service.get_customer(db, agent.id)
    assert c is None
