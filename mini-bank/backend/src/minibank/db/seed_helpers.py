"""Helpers for generating realistic Polish demo data.

- PESEL: 11-digit identifier with date-of-birth encoding + gender + checksum.
  Algorithm: weights 1,3,7,9,1,3,7,9,1,3 applied to first 10 digits;
  check digit = (10 - (sum mod 10)) mod 10.

- IBAN (PL/mBank): 28 chars, format 'PL CC BBBB BBBB AAAA AAAA AAAA AAAA'
  where CC = check digits mod 97, BBBBBBBB = bank prefix '11402004' for mBank.
"""

from __future__ import annotations

import secrets
from datetime import date


_PESEL_WEIGHTS = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]


def _encode_pesel_year_month(birth_date: date) -> str:
    """Encode YY + MM with century offset (1900: +0, 2000: +20, 1800: +80, 2100: +40, 2200: +60)."""
    year = birth_date.year
    month = birth_date.month
    if 1800 <= year <= 1899:
        month += 80
        yy = year - 1800
    elif 1900 <= year <= 1999:
        yy = year - 1900
    elif 2000 <= year <= 2099:
        month += 20
        yy = year - 2000
    elif 2100 <= year <= 2199:
        month += 40
        yy = year - 2100
    elif 2200 <= year <= 2299:
        month += 60
        yy = year - 2200
    else:
        raise ValueError(f"unsupported year {year}")
    return f"{yy:02d}{month:02d}"


def generate_pesel(birth_date: date, gender: str) -> str:
    """Generate a valid PESEL for the given DOB and gender ('M' or 'F').

    The serial (positions 7-9) is random; gender digit (position 10) is forced
    odd for M and even for F; checksum (position 11) is computed.
    """
    if gender not in ("M", "F"):
        raise ValueError("gender must be 'M' or 'F'")
    yymm = _encode_pesel_year_month(birth_date)
    day = f"{birth_date.day:02d}"
    serial = f"{secrets.randbelow(1000):03d}"
    gender_digit = secrets.randbelow(5) * 2 + (1 if gender == "M" else 0)
    first10 = yymm + day + serial + str(gender_digit)
    weighted = sum(int(d) * w for d, w in zip(first10, _PESEL_WEIGHTS))
    checksum = (10 - (weighted % 10)) % 10
    return first10 + str(checksum)


def is_valid_pesel_checksum(pesel: str) -> bool:
    """Verify the PESEL checksum (does not validate the date)."""
    if len(pesel) != 11 or not pesel.isdigit():
        return False
    weighted = sum(int(d) * w for d, w in zip(pesel[:10], _PESEL_WEIGHTS))
    return (10 - (weighted % 10)) % 10 == int(pesel[10])


def _iban_checksum_pl(bban: str) -> str:
    """Compute the 2-digit IBAN check for a Polish IBAN given the 24-digit BBAN."""
    # Move country code + '00' to the end, convert letters to digits, mod 97.
    rearranged = bban + "2521" + "00"  # 'PL' -> 25 21
    n = int(rearranged)
    check = 98 - (n % 97)
    return f"{check:02d}"


def generate_iban_pl_mbank(account_index: int) -> str:
    """Generate a deterministic mBank IBAN.

    BBAN = 11402004 + 16-digit account number derived from account_index.
    """
    bank = "11402004"
    account_num = f"{account_index:016d}"
    bban = bank + account_num
    check = _iban_checksum_pl(bban)
    return f"PL{check}{bban}"


def is_valid_iban(iban: str) -> bool:
    """Verify IBAN modulo-97 check. Strips spaces."""
    iban = iban.replace(" ", "").upper()
    if not iban.startswith("PL") or len(iban) != 28:
        return False
    rearranged = iban[4:] + iban[:4]
    converted = ""
    for ch in rearranged:
        if ch.isdigit():
            converted += ch
        elif ch.isalpha():
            converted += str(ord(ch) - 55)
        else:
            return False
    return int(converted) % 97 == 1
