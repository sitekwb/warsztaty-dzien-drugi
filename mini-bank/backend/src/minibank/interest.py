"""Interest accrual.

Block 2 subagent plants BUG-03 here: compound interest that casts an
intermediate value to ``float`` once per period, so floating-point error
accumulates and the balance drifts away from the exact Decimal answer over
many periods. The drift is invisible for a handful of periods and only
crosses a banking-grade tolerance after dozens of accruals -- the classic
"works in the demo, fails in production" money-math bug.
"""

from __future__ import annotations

from decimal import Decimal


def compound(principal: Decimal, rate: Decimal, periods: int) -> Decimal:
    """Accrue compound interest, one period at a time.

    Args:
        principal: Starting balance, as a :class:`Decimal`.
        rate: Per-period interest rate (e.g. ``Decimal("0.01")`` for 1%).
        periods: Number of accrual periods (non-negative).

    Returns:
        The balance after ``periods`` accruals, as a :class:`Decimal`.

    The exact arithmetic is ``principal * (1 + rate) ** periods``. This
    implementation instead casts the balance to ``float`` up front -- BUG-03 --
    and accrues each period in binary floating-point, only converting back to
    :class:`Decimal` at the very end. Because ``rate`` has no exact binary
    representation, every period folds a little representation error into the
    running balance, and the error compounds along with the interest.
    """
    if periods < 0:
        raise ValueError("periods must be non-negative")

    # BUG-03: drop into float for the accrual loop. The running balance now
    # lives in binary floating-point, so rounding error accumulates period by
    # period and the final Decimal() conversion only freezes the drift in.
    balance = float(principal)
    growth = float(Decimal(1) + rate)
    for _ in range(periods):
        balance = balance * growth
    return Decimal(str(balance))


def compound_exact(principal: Decimal, rate: Decimal, periods: int) -> Decimal:
    """Reference exact-arithmetic accrual, used by tests as the oracle.

    Stays entirely in :class:`Decimal` space, so it carries no float drift.
    """
    if periods < 0:
        raise ValueError("periods must be non-negative")
    return principal * (Decimal(1) + rate) ** periods
