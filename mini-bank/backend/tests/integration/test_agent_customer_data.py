"""Tests for agent access to customer accounts/transactions via X-Access-Grant-Id."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Account, Currency, Role, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "agcd.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        agent = User(email="ag@x.pl", password_hash=hash_password("pwd"), role=Role.AGENT, full_name="Ag")
        customer = User(email="c@x.pl", password_hash=hash_password("pwd"), role=Role.CUSTOMER, full_name="C")
        db.add_all([agent, customer])
        db.flush()
        acc = Account(
            owner_user_id=customer.id,
            holder_iban="PL12 1140 2004 0000 8888 8888 0001",
            balance=Decimal("250.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        db.add(acc)
        db.commit()
        customer_id = str(customer.id)

    from minibank.main import app
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": "ag@x.pl", "password": "pwd"})
    assert r.status_code == 200
    return c, customer_id


def test_get_customer_accounts_without_grant_401(client):
    c, customer_id = client
    r = c.get(f"/api/agent/customers/{customer_id}/accounts")
    assert r.status_code == 401


def test_get_customer_accounts_with_valid_grant(client):
    c, customer_id = client
    grant = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "T", "reason": "r", "ttl_minutes": 30},
    ).json()
    r = c.get(
        f"/api/agent/customers/{customer_id}/accounts",
        headers={"X-Access-Grant-Id": grant["id"]},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_customer_accounts_grant_wrong_customer_403(client):
    c, customer_id = client
    grant = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "T", "reason": "r", "ttl_minutes": 30},
    ).json()
    other = "11111111-1111-1111-1111-111111111111"
    r = c.get(
        f"/api/agent/customers/{other}/accounts",
        headers={"X-Access-Grant-Id": grant["id"]},
    )
    assert r.status_code == 403
