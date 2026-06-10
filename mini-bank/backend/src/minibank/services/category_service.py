"""Auto-kategoryzacja transakcji po regex na `title`.

Deterministyczna, pure function — żadnych LLM-call, żadnego stanu.
Kolejność reguł w `_RULES` jest częścią kontraktu (pierwszy match wygrywa).

WPLYWY nie ma własnej reguły — jest przypisywane w warstwie response
gdy transakcja jest przychodząca dla danego konta. Patrz services/account_service.compute_summary.
"""
from __future__ import annotations

import re

from minibank.db.models import TransactionCategory

# Pierwsza reguła która zmatchowała → kategoria. Wszystkie regex case-insensitive.
_RULES: list[tuple[TransactionCategory, re.Pattern[str]]] = [
    (TransactionCategory.SPOZYWCZE,
     re.compile(r"lidl|biedronka|kaufland|carrefour|auchan|żabka|zabka|tesco|netto", re.I)),
    (TransactionCategory.RESTAURACJE,
     re.compile(r"restauracja|pizza|sushi|kebab|uber.?eats|glovo|wolt|mcdonald|kfc|starbucks", re.I)),
    (TransactionCategory.TRANSPORT,
     re.compile(r"\buber\b|bolt|taxi|orlen|\bbp\b|shell|lotos|circle.?k|pkp|koleo|mzk|ztm|free.?now", re.I)),
    (TransactionCategory.TELEKOM,
     re.compile(r"orange|t-mobile|tmobile|play\b|plus\b|netia|upc|vectra|inea", re.I)),
    (TransactionCategory.RACHUNKI,
     re.compile(r"pgnig|tauron|enea|pge\b|energa|innogy|veolia|mpwik|opłata|oplata|czynsz|administracja", re.I)),
    (TransactionCategory.ROZRYWKA,
     re.compile(r"netflix|spotify|hbo|disney|cinema|kino|cineworld|empik|steam|playstation|xbox", re.I)),
    (TransactionCategory.PRZELEW_WLASNY,
     re.compile(r"przelew własny|przelew wlasny|own transfer|między kontami|miedzy kontami", re.I)),
]


def categorize(title: str | None) -> TransactionCategory:
    """Zwraca kategorię na podstawie regex po `title`. Brak match lub None → INNE."""
    if not title:
        return TransactionCategory.INNE
    for category, pattern in _RULES:
        if pattern.search(title):
            return category
    return TransactionCategory.INNE
