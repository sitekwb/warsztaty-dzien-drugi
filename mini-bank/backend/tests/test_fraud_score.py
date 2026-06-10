"""Tests for minibank.fraud_score.

Two jobs here:

1. A *characterisation test* that pins the current scoring behaviour of the
   god function. It passes on `main` today and is reused by Block 3's REF-01
   refactor as the safety net (refactor must not change the score).
2. An ``xfail`` test capturing planted BUG-04: a missing ``None`` guard on
   ``merchant_country`` raises ``AttributeError``.
"""

import pytest

from minibank.fraud_score import Transaction, score


def make_tx(**overrides) -> Transaction:
    base = dict(
        id="TX-1",
        amount=200.0,
        currency="PLN",
        merchant_id="MERCH-ORLEN",
        merchant_country="PL",
        dest_iban="PL61109010140000071219812874",
        hour_of_day=14,
        customer_avg_amount=180.0,
    )
    base.update(overrides)
    return Transaction(**base)


def test_low_risk_known_merchant_floors_at_zero():
    # Known-good merchant (-20) on an otherwise tame transaction clamps to 0.
    tx = make_tx()
    assert score(tx) == 0


def test_high_risk_country_adds_thirty():
    tx = make_tx(merchant_id="MERCH-UNKNOWN", merchant_country="NG")
    assert score(tx) == 30


def test_sanctioned_iban_and_large_amount_clamp_to_hundred():
    tx = make_tx(
        merchant_id="MERCH-UNKNOWN",
        merchant_country="PL",
        dest_iban="KP00000000000000000000000000",
        amount=15000.0,
        customer_avg_amount=100.0,
    )
    # 35 (large) + 25 (10x avg) + 60 (sanctioned IBAN) -> clamped to 100.
    assert score(tx) == 100


def test_characterisation_mixed_signals():
    # Pins an exact mid-range score across several heuristics. This is the
    # REF-01 safety net: the Block 3 refactor must keep this number stable.
    tx = make_tx(
        merchant_id="MERCH-UNKNOWN",
        merchant_country="RU",   # +30 high risk
        amount=6000.0,           # +20 medium absolute
        customer_avg_amount=1000.0,  # ratio 6 -> +15
        hour_of_day=3,           # +10 small hours
        dest_iban="DE89370400440532013000",  # not sanctioned
        flags=["new_device"],    # +10
    )
    assert score(tx) == 85


@pytest.mark.planted
@pytest.mark.xfail(reason="planted-BUG-04", strict=True)
def test_missing_merchant_country_is_scored():
    # A transaction with no merchant country should still be scored (treated
    # as unknown), not crash. BUG-04 makes score() raise AttributeError here.
    tx = make_tx(merchant_id="MERCH-UNKNOWN", merchant_country=None)
    result = score(tx)
    assert isinstance(result, int)
