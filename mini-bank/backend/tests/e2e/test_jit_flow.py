"""E2E flow: agent issues grant → reads customer accounts → revokes → 403."""

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
def two_clients(tmp_path, monkeypatch):
    db_file = tmp_path / "jit.db"
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
            holder_iban="PL12 1140 2004 0000 5555 5555 0001",
            balance=Decimal("999.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        db.add(acc)
        db.commit()
        customer_id = str(customer.id)

    from minibank.main import app
    ac = TestClient(app)
    ac.post("/api/auth/login", json={"email": "ag@x.pl", "password": "pwd"})
    return ac, customer_id


def test_jit_full_flow(two_clients):
    c, customer_id = two_clients
    g = c.post(
        "/api/agent/access-grants",
        json={"customer_id": customer_id, "ticket_id": "T-jit", "reason": "demo", "ttl_minutes": 30},
    ).json()
    grant_id = g["id"]

    r = c.get(
        f"/api/agent/customers/{customer_id}/accounts",
        headers={"X-Access-Grant-Id": grant_id},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1

    r2 = c.delete(f"/api/agent/access-grants/{grant_id}")
    assert r2.status_code == 200

    r3 = c.get(
        f"/api/agent/customers/{customer_id}/accounts",
        headers={"X-Access-Grant-Id": grant_id},
    )
    assert r3.status_code == 403
