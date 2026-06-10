"""Fraud scoring.

Block 2 authors this file as a deliberately messy "god function" -- it mixes
data lookup, scoring, and logging in one long body. It is the REF-01 refactor
target for Block 3 (do NOT refactor it here).

Block 2 also plants BUG-04 in it: a missing null check on
``transaction.merchant_country`` that raises ``AttributeError`` when the field
is ``None`` (an entirely realistic gap in upstream data).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("minibank.fraud")

# Toy reference data the god function reaches into directly. In real life this
# would be a service call; mixing it inline is part of why REF-01 exists.
HIGH_RISK_COUNTRIES = {"NG", "RU", "KP", "IR"}
SANCTIONED_IBAN_PREFIXES = {"KP", "IR", "SY"}
KNOWN_GOOD_MERCHANTS = {"MERCH-APPLE", "MERCH-IKEA", "MERCH-ORLEN"}


@dataclass
class Transaction:
    """Minimal transaction record fed to the scorer."""

    id: str
    amount: float
    currency: str
    merchant_id: str
    merchant_country: str | None
    dest_iban: str
    hour_of_day: int
    customer_avg_amount: float = 0.0
    flags: list[str] = field(default_factory=list)


def score(transaction: Transaction) -> int:
    """Return an integer fraud score (0-100) for a transaction.

    This is intentionally a god function: it looks up reference data, applies
    a pile of heuristics, logs intermediate state, and clamps the result --
    all in one place with no seams. Block 3's REF-01 exercise breaks it apart.

    BUG-04: ``transaction.merchant_country`` is dereferenced via ``.upper()``
    without a ``None`` guard, so a transaction whose merchant country is
    missing raises ``AttributeError`` instead of being scored.
    """
    logger.info("scoring transaction %s amount=%s", transaction.id, transaction.amount)

    risk = 0

    # --- amount-based heuristics -------------------------------------------
    if transaction.amount >= 10000:
        risk += 35
        logger.debug("tx %s: large absolute amount +35", transaction.id)
    elif transaction.amount >= 5000:
        risk += 20
        logger.debug("tx %s: medium absolute amount +20", transaction.id)
    elif transaction.amount >= 1000:
        risk += 8

    # Spend far above the customer's normal behaviour is suspicious.
    if transaction.customer_avg_amount > 0:
        ratio = transaction.amount / transaction.customer_avg_amount
        if ratio >= 10:
            risk += 25
            logger.debug("tx %s: 10x avg spend +25", transaction.id)
        elif ratio >= 5:
            risk += 15
        elif ratio >= 3:
            risk += 7

    # --- geography heuristics ----------------------------------------------
    # BUG-04: no None check before .upper(). Missing merchant_country crashes.
    country = transaction.merchant_country.upper()
    if country in HIGH_RISK_COUNTRIES:
        risk += 30
        logger.debug("tx %s: high-risk country %s +30", transaction.id, country)

    # --- sanctions screening on the destination IBAN -----------------------
    iban_country = (transaction.dest_iban or "")[:2].upper()
    if iban_country in SANCTIONED_IBAN_PREFIXES:
        risk += 60
        logger.warning("tx %s: sanctioned IBAN prefix %s +60", transaction.id, iban_country)

    # --- time-of-day heuristics --------------------------------------------
    if 1 <= transaction.hour_of_day <= 4:
        risk += 10
        logger.debug("tx %s: small-hours timing +10", transaction.id)

    # --- merchant allow-list -----------------------------------------------
    if transaction.merchant_id in KNOWN_GOOD_MERCHANTS:
        risk -= 20
        logger.debug("tx %s: known-good merchant -20", transaction.id)

    # --- explicit upstream flags -------------------------------------------
    if "chargeback_history" in transaction.flags:
        risk += 15
    if "new_device" in transaction.flags:
        risk += 10

    # --- clamp to 0..100 ----------------------------------------------------
    if risk < 0:
        risk = 0
    if risk > 100:
        risk = 100

    logger.info("tx %s: final fraud score %d", transaction.id, risk)
    return risk
