"""TDD tests for minibank.timezone_check (BUG-02: closed account treated active).

The exercise (B3, "Find the bug you can't see") asks attendees to use
`superpowers:systematic-debugging` to locate why a *closed* account is treated
as *active* under one specific UTC offset and time window, so interest could
wrongly accrue.

On the `main` branch the root-cause test is tagged xfail(planted-BUG-02); the
canonical fix lands on the `solutions` branch and removes the marker.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from minibank.timezone_check import is_account_active_at


# --- A closing day in UTC ---------------------------------------------------
CLOSED_ON = date(2026, 5, 16)


def _open_account_record(closed_on: date | None = CLOSED_ON) -> dict:
    """Minimal account record: opened well before, closed end-of-day CLOSED_ON."""
    return {"opened_on": date(2024, 1, 1), "closed_on": closed_on}


def test_open_account_is_active_when_never_closed():
    """An account that was never closed is always active."""
    account = _open_account_record(closed_on=None)
    instant = datetime(2026, 5, 16, 23, 0, tzinfo=timezone.utc)
    assert is_account_active_at(account, instant) is True


def test_account_is_active_before_its_closing_day():
    """Before the closing day the account is active in every timezone."""
    account = _open_account_record()
    instant = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    assert is_account_active_at(account, instant) is True


def test_account_is_inactive_well_after_closing_day_in_utc():
    """A full UTC day after closing, the account is inactive."""
    account = _open_account_record()
    instant = datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc)
    assert is_account_active_at(account, instant) is False


def test_naive_instant_is_rejected():
    """The contract requires an aware datetime so offsets are explicit."""
    account = _open_account_record()
    naive = datetime(2026, 5, 17, 1, 0)  # no tzinfo
    with pytest.raises(ValueError):
        is_account_active_at(account, naive)


@pytest.mark.xfail(reason="planted-BUG-02", strict=True)
def test_closed_account_not_active_just_after_midnight_at_positive_offset():
    """Root-cause: BUG-02 closed-account-treated-active across timezones.

    The account closed end-of-day 2026-05-16 (UTC). Consider an instant a few
    minutes after midnight UTC on 2026-05-17 -- i.e. the day AFTER closing.
    Observed from a +02:00 zone (e.g. Europe/Warsaw in summer), the wall-clock
    local date is still 2026-05-17, so the account is unambiguously closed.

    The buggy implementation derives a *local naive date* by adding the offset
    and, at a positive offset within the window just after UTC midnight, lands
    back on the closing day 2026-05-16 and reports the account as still active.
    A correct implementation reports inactive in every timezone here.
    """
    account = _open_account_record()
    warsaw_summer = timezone(timedelta(hours=2))
    # 00:30 UTC on 2026-05-17 (the day AFTER closing) == 02:30 local at +02:00.
    instant = datetime(2026, 5, 17, 0, 30, tzinfo=timezone.utc).astimezone(warsaw_summer)
    assert instant.date() == date(2026, 5, 17)  # local wall-clock is the day after
    assert is_account_active_at(account, instant) is False
