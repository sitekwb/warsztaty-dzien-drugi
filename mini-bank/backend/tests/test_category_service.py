"""Testy deterministycznej kategoryzacji po `title`."""
import pytest

from minibank.db.models import TransactionCategory
from minibank.services.category_service import categorize


@pytest.mark.parametrize("title,expected", [
    ("Lidl Warszawa", TransactionCategory.SPOZYWCZE),
    ("BIEDRONKA 4521", TransactionCategory.SPOZYWCZE),
    ("Pizza Hut Mokotów", TransactionCategory.RESTAURACJE),
    ("Uber Eats zamówienie", TransactionCategory.RESTAURACJE),
    ("Orlen stacja 12", TransactionCategory.TRANSPORT),
    ("Uber przejazd", TransactionCategory.TRANSPORT),
    ("Orange faktura", TransactionCategory.TELEKOM),
    ("Tauron prąd 03/26", TransactionCategory.RACHUNKI),
    ("Netflix subscription", TransactionCategory.ROZRYWKA),
    ("Playstation 5", TransactionCategory.ROZRYWKA),
    ("Przelew własny między kontami", TransactionCategory.PRZELEW_WLASNY),
    ("Random gibberish 12345", TransactionCategory.INNE),
])
def test_categorize_known_titles(title: str, expected: TransactionCategory):
    assert categorize(title) is expected


def test_categorize_none_title():
    assert categorize(None) is TransactionCategory.INNE


def test_categorize_empty_title():
    assert categorize("") is TransactionCategory.INNE


def test_categorize_case_insensitive():
    assert categorize("lidl") is categorize("LIDL") is TransactionCategory.SPOZYWCZE


def test_categorize_first_match_wins():
    # 'kino' wpada do ROZRYWKA przed jakimkolwiek INNE-fallbackiem
    assert categorize("Wieczór kino z rodziną") is TransactionCategory.ROZRYWKA
