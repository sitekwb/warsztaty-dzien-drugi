"""Tests for auth_service: bcrypt hashing, JWT encode/decode, login flow."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Role, User
from minibank.services import auth_service


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


def test_hash_password_then_verify():
    h = auth_service.hash_password("Demo1234!")
    assert auth_service.verify_password("Demo1234!", h) is True
    assert auth_service.verify_password("wrong", h) is False


def test_encode_then_decode_jwt():
    token = auth_service.encode_jwt(user_id="abc", role="customer")
    payload = auth_service.decode_jwt(token)
    assert payload["sub"] == "abc"
    assert payload["role"] == "customer"


def test_authenticate_user_success(db):
    u = User(
        email="user@x.pl",
        password_hash=auth_service.hash_password("pwd"),
        role=Role.CUSTOMER,
        full_name="X",
    )
    db.add(u)
    db.commit()
    result = auth_service.authenticate(db, "user@x.pl", "pwd")
    assert result is not None
    assert result.email == "user@x.pl"


def test_authenticate_user_wrong_password(db):
    u = User(
        email="user@x.pl",
        password_hash=auth_service.hash_password("pwd"),
        role=Role.CUSTOMER,
        full_name="X",
    )
    db.add(u)
    db.commit()
    result = auth_service.authenticate(db, "user@x.pl", "WRONG")
    assert result is None


def test_authenticate_unknown_email(db):
    result = auth_service.authenticate(db, "noone@x.pl", "x")
    assert result is None
