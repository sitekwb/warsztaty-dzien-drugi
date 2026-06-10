"""Tests for access_grant_service: create, list active, revoke, is_active_grant.

BUG-06 lives here: `is_active_grant` does not check `expires_at < now`.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import JitAccessGrant, Role, User
from minibank.services import access_grant_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        agent = User(email="ag@x.pl", password_hash="x", role=Role.AGENT, full_name="Ag")
        customer = User(email="c@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="Cu")
        s.add_all([agent, customer])
        s.commit()
        s.refresh(agent); s.refresh(customer)
        yield s, agent, customer


def test_create_grant_default_ttl(db):
    sess, agent, customer = db
    grant = access_grant_service.create_grant(
        sess,
        agent_user_id=agent.id,
        customer_id=customer.id,
        ticket_id="TCK-1",
        reason="Investigate dispute",
        ttl_minutes=30,
    )
    sess.commit()
    assert grant.id is not None
    delta = (grant.expires_at - grant.granted_at).total_seconds()
    assert 1799 < delta < 1801  # ~30 minutes


def test_list_active_excludes_revoked(db):
    sess, agent, customer = db
    g = access_grant_service.create_grant(
        sess, agent_user_id=agent.id, customer_id=customer.id, ticket_id="T", reason="r", ttl_minutes=30
    )
    sess.commit()
    access_grant_service.revoke_grant(sess, grant_id=g.id, agent_user_id=agent.id)
    sess.commit()
    active = access_grant_service.list_active_for_agent(sess, agent_user_id=agent.id)
    assert len(active) == 0


def test_is_active_grant_happy_path(db):
    sess, agent, customer = db
    g = access_grant_service.create_grant(
        sess, agent_user_id=agent.id, customer_id=customer.id, ticket_id="T", reason="r", ttl_minutes=30
    )
    sess.commit()
    assert access_grant_service.is_active_grant(sess, grant_id=g.id, customer_id=customer.id) is True


def test_is_active_grant_wrong_customer(db):
    sess, agent, customer = db
    g = access_grant_service.create_grant(
        sess, agent_user_id=agent.id, customer_id=customer.id, ticket_id="T", reason="r", ttl_minutes=30
    )
    sess.commit()
    other = uuid4()
    assert access_grant_service.is_active_grant(sess, grant_id=g.id, customer_id=other) is False


def test_is_active_grant_unknown_grant(db):
    sess, _agent, customer = db
    assert access_grant_service.is_active_grant(sess, grant_id=uuid4(), customer_id=customer.id) is False


def test_is_active_grant_revoked(db):
    sess, agent, customer = db
    g = access_grant_service.create_grant(
        sess, agent_user_id=agent.id, customer_id=customer.id, ticket_id="T", reason="r", ttl_minutes=30
    )
    sess.commit()
    access_grant_service.revoke_grant(sess, grant_id=g.id, agent_user_id=agent.id)
    sess.commit()
    assert access_grant_service.is_active_grant(sess, grant_id=g.id, customer_id=customer.id) is False


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-06: is_active_grant does not check expires_at; expired grants stay active",
    strict=False,
)
def test_is_active_grant_expired_BUG_06(db):
    """An expired grant must NOT be active. With BUG-06 the service still
    returns True because it only checks revoked_at, not expires_at."""
    sess, agent, customer = db
    expired = JitAccessGrant(
        agent_user_id=agent.id,
        customer_user_id=customer.id,
        ticket_id="OLD",
        reason="expired ticket",
        granted_at=datetime.now(timezone.utc) - timedelta(hours=2),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    sess.add(expired)
    sess.commit()
    sess.refresh(expired)
    assert access_grant_service.is_active_grant(sess, grant_id=expired.id, customer_id=customer.id) is False
