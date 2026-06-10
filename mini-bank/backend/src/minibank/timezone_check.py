"""Timezone handling for account activity windows.

Block 3 plants BUG-02 here: a closed account is incorrectly treated as still
active under one specific UTC offset and time window (just after UTC midnight
at a positive offset), so interest could wrongly accrue.

The exercise "Find the bug you can't see" uses ``superpowers:systematic-debugging``
to locate the root cause; the canonical fix lands on the ``solutions`` branch.

Self-contained: this module does not touch ``interest.py`` or ``fraud_score.py``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def _local_business_date(instant: datetime) -> date:
    """Return the business-calendar date for an aware ``instant``.

    BUG-02 lives here. The intent is to obtain the local wall-clock date so an
    account's closing day can be compared on the calendar the customer sees.
    The implementation first normalises the instant to UTC (correct) but then
    *also subtracts the original offset* before taking the date -- applying the
    timezone conversion a second time. This double conversion is the inverse of
    what is needed; the offset should be added back, not subtracted.

    For most instants the doubled shift stays within the same calendar day and
    the error is invisible. But for an instant just after midnight UTC observed
    from a positive offset, the double subtraction pushes the date back across
    midnight onto the *previous* day -- which can be the closing day -- so a
    closed account looks active and interest keeps accruing.

    A correct implementation would convert to UTC once and use that date, e.g.
    ``instant.astimezone(timezone.utc).date()``.
    """
    offset = instant.utcoffset() or timedelta(0)
    utc_instant = instant.astimezone(timezone.utc)
    return (utc_instant - offset).date()


def is_account_active_at(account: dict, instant: datetime) -> bool:
    """Return whether ``account`` is active at ``instant``.

    ``account`` carries ``opened_on`` and ``closed_on`` (a ``date`` or ``None``).
    An account is active from its opening day through the end of its closing day
    (inclusive); the day after ``closed_on`` it is inactive.

    ``instant`` must be timezone-aware so the offset is explicit.
    """
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("instant must be timezone-aware")

    business_date = _local_business_date(instant)

    opened_on: date = account["opened_on"]
    if business_date < opened_on:
        return False

    closed_on: date | None = account.get("closed_on")
    if closed_on is None:
        return True

    return business_date <= closed_on
