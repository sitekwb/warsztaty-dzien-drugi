"""Tests for idempotency middleware. BUG-09 planted: cache by key only,
not (key + request_hash)."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import IdempotencyKey, Role, User
from minibank.middleware.idempotency import (
    cache_lookup,
    cache_store,
    compute_request_hash,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        u = User(email="u@x.pl", password_hash="x", role=Role.CUSTOMER, full_name="U")
        s.add(u); s.commit(); s.refresh(u)
        s.user_id = u.id
        yield s


def test_cache_lookup_miss_returns_none(db):
    assert cache_lookup(db, key=uuid4(), request_hash="x") == (None, None)


def test_cache_store_then_lookup_hits(db):
    k = uuid4()
    rh = compute_request_hash({"a": 1})
    cache_store(db, key=k, user_id=db.user_id, request_hash=rh,
                response_body={"ok": True}, status_code=201)
    db.commit()
    body, status = cache_lookup(db, key=k, request_hash=rh)
    assert status == 201
    assert body == {"ok": True}


def test_request_hash_canonical(db):
    h1 = compute_request_hash({"a": 1, "b": 2})
    h2 = compute_request_hash({"b": 2, "a": 1})
    assert h1 == h2


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-09: cache_lookup ignores request_hash mismatch — returns stale response",
    strict=False,
)
def test_cache_lookup_different_payload_returns_conflict_BUG_09(db):
    """Stripe spec: same key + different payload → 409 Conflict. With BUG-09 we
    return the original response."""
    k = uuid4()
    rh1 = compute_request_hash({"a": 1})
    cache_store(db, key=k, user_id=db.user_id, request_hash=rh1,
                response_body={"x": 1}, status_code=201)
    db.commit()
    body, status = cache_lookup(db, key=k, request_hash=compute_request_hash({"a": 2}))
    assert status == 409
