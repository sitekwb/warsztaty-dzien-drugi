"""Tests for sca_service. BUG-08 lives in verify(): missing linked_amount/iban check."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from minibank.db.base import Base
from minibank.db.models import Role, User
from minibank.services import sca_service


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


def test_create_challenge_returns_code_and_id(db):
    ch, code = sca_service.create_challenge(
        db, user_id=db.user_id, amount=Decimal("250.00"),
        dest_iban="PL12 1140 0000", pending_payload={"x": 1},
    )
    db.commit()
    assert ch.id is not None
    assert len(code) == 6 and code.isdigit()
    assert ch.linked_amount == Decimal("250.00")


def test_verify_correct_code_returns_payload(db):
    ch, code = sca_service.create_challenge(
        db, user_id=db.user_id, amount=Decimal("250.00"),
        dest_iban="PL12 1140 0000", pending_payload={"x": 1},
    )
    db.commit()
    payload = sca_service.verify(
        db, challenge_id=ch.id, code=code,
        request_amount=Decimal("250.00"), request_dest_iban="PL12 1140 0000",
    )
    assert payload == {"x": 1}


def test_verify_wrong_code(db):
    ch, _ = sca_service.create_challenge(
        db, user_id=db.user_id, amount=Decimal("250.00"),
        dest_iban="PL12 1140 0000", pending_payload={"x": 1},
    )
    db.commit()
    with pytest.raises(sca_service.ScaError):
        sca_service.verify(db, challenge_id=ch.id, code="000000",
                           request_amount=Decimal("250.00"),
                           request_dest_iban="PL12 1140 0000")


def test_verify_used_challenge_rejected(db):
    ch, code = sca_service.create_challenge(
        db, user_id=db.user_id, amount=Decimal("250.00"),
        dest_iban="PL12 1140 0000", pending_payload={"x": 1},
    )
    db.commit()
    sca_service.verify(db, challenge_id=ch.id, code=code,
                       request_amount=Decimal("250.00"),
                       request_dest_iban="PL12 1140 0000")
    db.commit()
    with pytest.raises(sca_service.ScaError):
        sca_service.verify(db, challenge_id=ch.id, code=code,
                           request_amount=Decimal("250.00"),
                           request_dest_iban="PL12 1140 0000")


@pytest.mark.planted
@pytest.mark.xfail(
    reason="BUG-08: verify() does not check linked_amount/iban — bypass possible",
    strict=False,
)
def test_verify_amount_mismatch_rejected_BUG_08(db):
    """PSD2 dynamic linking: code is valid only for the (amount, iban) pair
    used when the challenge was created. BUG-08 ignores the mismatch."""
    ch, code = sca_service.create_challenge(
        db, user_id=db.user_id, amount=Decimal("250.00"),
        dest_iban="PL12 1140 0000", pending_payload={"x": 1},
    )
    db.commit()
    with pytest.raises(sca_service.ScaError):
        sca_service.verify(db, challenge_id=ch.id, code=code,
                           request_amount=Decimal("5000.00"),
                           request_dest_iban="PL12 1140 0000")
