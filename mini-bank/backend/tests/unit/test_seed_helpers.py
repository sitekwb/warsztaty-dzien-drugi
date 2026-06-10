"""Tests for PESEL + IBAN generators used by seed.py."""

from datetime import date

from minibank.db.seed_helpers import (
    generate_pesel,
    is_valid_pesel_checksum,
    generate_iban_pl_mbank,
    is_valid_iban,
)


def test_generate_pesel_valid_checksum():
    p = generate_pesel(birth_date=date(1985, 6, 12), gender="M")
    assert len(p) == 11
    assert is_valid_pesel_checksum(p)


def test_generate_pesel_female_digit():
    # Position 10 (0-indexed 9): even for female, odd for male.
    p = generate_pesel(birth_date=date(1990, 4, 1), gender="F")
    assert int(p[9]) % 2 == 0


def test_generate_pesel_male_digit():
    p = generate_pesel(birth_date=date(1990, 4, 1), gender="M")
    assert int(p[9]) % 2 == 1


def test_generate_iban_pl_mbank_starts_with_pl():
    iban = generate_iban_pl_mbank(account_index=42)
    assert iban.startswith("PL")
    assert "1140" in iban  # mBank prefix
    assert is_valid_iban(iban)


def test_iban_validation_rejects_garbage():
    assert not is_valid_iban("PL00 0000 0000 0000 0000 0000 0000")
