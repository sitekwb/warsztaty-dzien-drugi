"""Integration tests for GET /api/accounts/{id}/summary and category w transactions response."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import (
    Account,
    Currency,
    Role,
    Transaction,
    TransactionCategory,
    TransactionStatus,
    User,
)
from minibank.services.auth_service import hash_password


def _setup_db(tmp_path, monkeypatch, file_name: str):
    db_file = tmp_path / file_name
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    return session_module.SessionLocal


def _seed(session_local):
    """Seed: 1 customer A z 1 kontem, 1 customer B z 1 kontem. 3 outflow tx (różne kategorie) + 1 inflow tx."""
    with session_local() as db:
        a = User(email="a@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="A")
        b = User(email="b@x.pl", password_hash=hash_password("pwd"),
                 role=Role.CUSTOMER, full_name="B")
        db.add_all([a, b]); db.flush()
        acc_a = Account(
            owner_user_id=a.id,
            holder_iban="PL12 1140 2004 0000 0000 0000 0001",
            balance=Decimal("1000.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        acc_b = Account(
            owner_user_id=b.id,
            holder_iban="PL12 1140 2004 0000 0000 0000 0002",
            balance=Decimal("1000.00"),
            currency=Currency.PLN,
            opened_on=date(2024, 1, 1),
        )
        db.add_all([acc_a, acc_b]); db.flush()
        now = datetime.now(timezone.utc)
        # 3 wydatki różne kategorie, 1 wpływ
        db.add_all([
            Transaction(source_account_id=acc_a.id, dest_iban="PL99...", amount=Decimal("100"),
                        currency=Currency.PLN, title="Lidl", status=TransactionStatus.COMPLETED.value,
                        initiated_by_user_id=a.id, recipient_name="Lidl SA",
                        category=TransactionCategory.SPOZYWCZE, created_at=now),
            Transaction(source_account_id=acc_a.id, dest_iban="PL98...", amount=Decimal("50"),
                        currency=Currency.PLN, title="Orlen", status=TransactionStatus.COMPLETED.value,
                        initiated_by_user_id=a.id, recipient_name="Orlen SA",
                        category=TransactionCategory.TRANSPORT, created_at=now),
            Transaction(source_account_id=acc_a.id, dest_iban="PL97...", amount=Decimal("30"),
                        currency=Currency.PLN, title="Netflix", status=TransactionStatus.COMPLETED.value,
                        initiated_by_user_id=a.id, recipient_name="Netflix",
                        category=TransactionCategory.ROZRYWKA, created_at=now),
            # Inflow z konta B → A
            Transaction(source_account_id=acc_b.id, dest_account_id=acc_a.id,
                        amount=Decimal("200"), currency=Currency.PLN,
                        title="Zwrot", status=TransactionStatus.COMPLETED.value,
                        initiated_by_user_id=b.id, recipient_name="A",
                        category=TransactionCategory.INNE, created_at=now),
        ])
        db.commit()
        return str(acc_a.id), str(acc_b.id), "a@x.pl", "b@x.pl"


@pytest.fixture
def env(tmp_path, monkeypatch):
    SL = _setup_db(tmp_path, monkeypatch, "summary.db")
    acc_a_id, acc_b_id, email_a, email_b = _seed(SL)
    from minibank.main import app
    return {
        "client": TestClient(app),
        "acc_a_id": acc_a_id,
        "acc_b_id": acc_b_id,
        "email_a": email_a,
        "email_b": email_b,
    }


def _login(client: TestClient, email: str):
    r = client.post("/api/auth/login", json={"email": email, "password": "pwd"})
    assert r.status_code == 200, r.text


def test_summary_unauthenticated(env):
    r = env["client"].get(f"/api/accounts/{env['acc_a_id']}/summary")
    assert r.status_code == 401


def test_summary_invalid_month_format(env):
    _login(env["client"], env["email_a"])
    r = env["client"].get(f"/api/accounts/{env['acc_a_id']}/summary?month=2026-bad")
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert isinstance(detail, list) and detail[0]["loc"][-1] == "month"


def test_summary_other_users_account_returns_404(env):
    _login(env["client"], env["email_a"])
    r = env["client"].get(f"/api/accounts/{env['acc_b_id']}/summary")
    assert r.status_code == 404


def test_summary_own_account_returns_structure(env):
    _login(env["client"], env["email_a"])
    now = datetime.now(timezone.utc)
    month = f"{now.year:04d}-{now.month:02d}"
    r = env["client"].get(f"/api/accounts/{env['acc_a_id']}/summary?month={month}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["month"] == month
    assert Decimal(body["inflow"]) == Decimal("200")
    assert Decimal(body["outflow"]) == Decimal("180")
    assert Decimal(body["mtd_balance"]) == Decimal("20")
    assert isinstance(body["by_category"], list)
    # by_category bez WPLYWY/PRZELEW_WLASNY
    cats = [item["category"] for item in body["by_category"]]
    assert "WPLYWY" not in cats and "PRZELEW_WLASNY" not in cats
    # DESC po total: SPOZYWCZE 100 > TRANSPORT 50 > ROZRYWKA 30
    totals = [Decimal(item["total"]) for item in body["by_category"]]
    assert totals == sorted(totals, reverse=True)
    assert cats[0] == "SPOZYWCZE"


def test_summary_default_month_is_current_utc(env):
    _login(env["client"], env["email_a"])
    r = env["client"].get(f"/api/accounts/{env['acc_a_id']}/summary")
    assert r.status_code == 200
    now = datetime.now(timezone.utc)
    assert r.json()["month"] == f"{now.year:04d}-{now.month:02d}"


def test_transactions_response_has_category_with_wplywy_remap(env):
    _login(env["client"], env["email_a"])
    r = env["client"].get(f"/api/accounts/{env['acc_a_id']}/transactions")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 4  # 3 outflow + 1 inflow (bidirectional)
    # Inflow (z B → A) ma category=WPLYWY w response, niezależnie od DB INNE
    incoming = [row for row in rows if row.get("dest_account_id") == env["acc_a_id"]]
    assert len(incoming) == 1
    assert incoming[0]["category"] == "WPLYWY"
    # Outflows mają oryginalne kategorie
    outgoing = [row for row in rows if row.get("source_account_id") == env["acc_a_id"]]
    cats = {row["category"] for row in outgoing}
    assert cats == {"SPOZYWCZE", "TRANSPORT", "ROZRYWKA"}
