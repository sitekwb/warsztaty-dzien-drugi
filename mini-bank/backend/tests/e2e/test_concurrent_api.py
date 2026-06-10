"""End-to-end demonstration of BUG-01 via HTTP.

Two concurrent POST /api/transfers from the same source account both pass the
overdraft check before either commits. With BUG-01 active in the service layer,
this reliably overdraws the account beyond its overdraft_limit.

This test is marked `xfail` on main (bug active). The fix lands in v2+ on
the `solutions` branch and the xfail flips to xpass.
"""

from concurrent.futures import ThreadPoolExecutor
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
    db_file = tmp_path / "e2e.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as db:
        u = User(
            email="e2e@minibank.pl",
            password_hash=hash_password("pwd"),
            role=Role.CUSTOMER,
            full_name="E2E User",
        )
        db.add(u)
        db.flush()
        src = Account(
            owner_user_id=u.id,
            holder_iban="PL12 1140 2004 0000 9999 9999 0001",
            balance=Decimal("100.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        dst = Account(
            owner_user_id=u.id,
            holder_iban="PL12 1140 2004 0000 9999 9999 0002",
            balance=Decimal("0.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        db.add_all([src, dst])
        db.commit()
        src_id = str(src.id)
        dst_iban = dst.holder_iban

    from minibank.main import app
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"email": "e2e@minibank.pl", "password": "pwd"})
    assert r.status_code == 200
    return c, src_id, dst_iban


@pytest.mark.planted
@pytest.mark.xfail(reason="BUG-01: concurrent transfers race past the overdraft check", strict=False)
def test_concurrent_transfers_overdraw_account(client):
    c, src_id, dst_iban = client

    def transfer():
        return c.post(
            "/api/transfers",
            json={
                "source_account_id": src_id,
                "dest_iban": dst_iban,
                "amount": "80.00",
                "currency": "PLN",
                "title": "race",
                "recipient_name": "Test Odbiorca",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(transfer) for _ in range(2)]
        results = [f.result() for f in futures]

    # Both calls returned 201 — the bug.
    assert all(r.status_code in (201, 202) for r in results), (
        f"expected both to succeed: statuses {[r.status_code for r in results]}"
    )

    # Read final balance via /api/accounts. After two 80 PLN debits the balance
    # would be -60 PLN, which exceeds the default 0 overdraft_limit.
    r = c.get("/api/accounts")
    accounts = r.json()
    src = next(a for a in accounts if a["id"] == src_id)
    assert Decimal(src["balance"]) >= Decimal("0"), (
        f"BUG-01 reproduced: balance {src['balance']} < 0 means both transfers debited"
    )
