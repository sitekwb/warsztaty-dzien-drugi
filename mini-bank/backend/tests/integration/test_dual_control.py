"""Large transfers require dual approval before completion."""

import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db import session as session_module
from minibank.db.models import Account, Currency, Role, Transaction, User
from minibank.services.auth_service import hash_password


@pytest.fixture
def env(tmp_path, monkeypatch):
    db_file = tmp_path / "dc.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    from minibank.config import get_settings
    get_settings.cache_clear()
    session_module.engine = session_module._make_engine()
    session_module.SessionLocal = session_module._make_session_local(session_module.engine)
    Base.metadata.create_all(session_module.engine)
    with session_module.SessionLocal() as db:
        sup = User(email="sup@x.pl", password_hash=hash_password("pwd"),
                   role=Role.SUPERVISOR, full_name="Sup")
        cu = User(email="c@x.pl", password_hash=hash_password("pwd"),
                  role=Role.CUSTOMER, full_name="C")
        db.add_all([sup, cu]); db.flush()
        src = Account(owner_user_id=cu.id, holder_iban="PL12 1140 2004 0000 0000 0000 0001",
                      balance=Decimal("100000.00"), currency=Currency.PLN, opened_on=date(2024, 1, 1))
        dst = Account(owner_user_id=cu.id, holder_iban="PL12 1140 2004 0000 0000 0000 0002",
                      balance=Decimal("0"), currency=Currency.PLN, opened_on=date(2024, 1, 1))
        db.add_all([src, dst]); db.commit()
        src_id = str(src.id); dst_iban = dst.holder_iban
    from minibank.main import app
    return app, src_id, dst_iban


def test_large_transfer_pending_dual_approval(env):
    app, src_id, dst_iban = env
    cu_client = TestClient(app)
    cu_client.post("/api/auth/login", json={"email": "c@x.pl", "password": "pwd"})
    r = cu_client.post("/api/transfers", json={
        "source_account_id": src_id, "dest_iban": dst_iban,
        "amount": "60000.00", "currency": "PLN", "title": "duzy",
        "recipient_name": "Test Odbiorca"})
    assert r.status_code == 202
    challenge_id = r.json()["sca_challenge_id"]

    # Get OTP code from notifications
    notes = cu_client.get("/api/notifications/me").json()
    code = "".join(ch for ch in notes[0]["body"] if ch.isdigit())[-6:]

    r2 = cu_client.post(f"/api/sca/challenges/{challenge_id}/verify", json={"code": code})
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "requires_dual_approval"
    tx_id = body["transaction_id"]

    sup_client = TestClient(app)
    sup_client.post("/api/auth/login", json={"email": "sup@x.pl", "password": "pwd"})
    r3 = sup_client.get("/api/agent/supervisor/review-queue")
    assert r3.status_code == 200
    assert any(t["id"] == tx_id for t in r3.json())

    r4 = sup_client.post(f"/api/transfers/{tx_id}/approve")
    assert r4.status_code == 200

    with session_module.SessionLocal() as db:
        import uuid
        t = db.get(Transaction, uuid.UUID(tx_id))
    assert t.status == "completed"
    assert t.approved_by_user_id is not None
