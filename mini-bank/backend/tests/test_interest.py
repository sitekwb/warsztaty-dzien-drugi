"""Tests for minibank.interest (compound interest accrual).

TDD discipline: these tests pin the exact-arithmetic contract for compound
interest. The planted BUG-03 (a per-period float cast) is captured by an
``xfail`` test that demonstrates drift beyond a banking-grade tolerance over
many periods.
"""

from decimal import Decimal

import pytest

from minibank.interest import compound, compound_exact

# Banking-grade tolerance: one hundredth of a cent.
TOL = Decimal("0.0001")


def test_zero_periods_returns_principal():
    principal = Decimal("1000.00")
    assert compound(principal, Decimal("0.05"), 0) == principal


def test_negative_periods_rejected():
    with pytest.raises(ValueError):
        compound(Decimal("100"), Decimal("0.01"), -1)


def test_single_period_matches_exact():
    # One period has no room to accumulate drift.
    result = compound(Decimal("1000.00"), Decimal("0.01"), 1)
    expected = compound_exact(Decimal("1000.00"), Decimal("0.01"), 1)
    assert abs(result - expected) < TOL


def test_few_periods_within_tolerance():
    # A handful of periods stays within tolerance -- this is why the bug
    # survives a quick demo.
    result = compound(Decimal("1000.00"), Decimal("0.01"), 3)
    expected = compound_exact(Decimal("1000.00"), Decimal("0.01"), 3)
    assert abs(result - expected) < TOL


def test_exact_oracle_is_pure_decimal():
    # The oracle itself must never drift, regardless of period count.
    a = compound_exact(Decimal("1000.00"), Decimal("0.01"), 240)
    b = Decimal("1000.00") * (Decimal("1") + Decimal("0.01")) ** 240
    assert a == b


@pytest.mark.planted
@pytest.mark.xfail(reason="planted-BUG-03", strict=True)
def test_treasury_balance_many_periods_within_tolerance():
    # A treasury-scale balance accrued daily over a long horizon. The float
    # accumulator in compound() folds in binary rounding error every period;
    # at this scale the drift exceeds TOL (a hundredth of a cent), so this
    # fails on `main`. A few periods on a retail balance hide it -- which is
    # exactly why the bug survives a quick demo.
    principal = Decimal("100000000.00")
    rate = Decimal("0.01")
    periods = 600
    result = compound(principal, rate, periods)
    expected = compound_exact(principal, rate, periods)
    assert abs(result - expected) < TOL
