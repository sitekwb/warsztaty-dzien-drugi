"""Tests for v2 ORM models — AuditLogEntry, JitAccessGrant."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import (
    AuditLogEntry,
    JitAccessGrant,
    Role,
    User,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


def test_audit_log_entry_with_payload(session):
    actor = User(email="a@x.pl", password_hash="x", role=Role.AGENT, full_name="A")
    session.add(actor)
    session.flush()
    entry = AuditLogEntry(
        actor_user_id=actor.id,
        action="transfer_initiated",
        target_type="transaction",
        payload={"amount": "100.00"},
    )
    session.add(entry)
    session.commit()
    assert entry.id is not None
    assert entry.payload == {"amount": "100.00"}
    assert entry.ts.tzinfo is not None


def test_jit_access_grant_fields(session):
    agent = User(email="a@x.pl", password_hash="x", role=Role.AGENT, full_name="A")
    customer = User(email="c@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="C")
    session.add_all([agent, customer])
    session.flush()
    now = datetime.now(timezone.utc)
    grant = JitAccessGrant(
        agent_user_id=agent.id,
        customer_user_id=customer.id,
        ticket_id="TCK-1234",
        reason="Customer reported suspicious transaction",
        expires_at=now + timedelta(minutes=30),
    )
    session.add(grant)
    session.commit()
    assert grant.id is not None
    assert grant.ticket_id == "TCK-1234"
    assert grant.revoked_at is None
    assert grant.granted_at is not None
