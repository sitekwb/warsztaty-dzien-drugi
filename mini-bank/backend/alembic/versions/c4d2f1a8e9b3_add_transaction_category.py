"""add transaction_category enum + transactions.category NOT NULL z backfillem

Revision ID: c4d2f1a8e9b3
Revises: 3b03352b7de3
Create Date: 2026-05-27 13:00:00.000000
"""
from __future__ import annotations

import hashlib
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d2f1a8e9b3"
down_revision: Union[str, Sequence[str], None] = "3b03352b7de3"
branch_labels = None
depends_on = None


_CATEGORY_LABELS = [
    "SPOZYWCZE", "RESTAURACJE", "TRANSPORT", "TELEKOM",
    "RACHUNKI", "ROZRYWKA", "PRZELEW_WLASNY", "WPLYWY", "INNE",
]

_BACKFILL_RULES: list[tuple[str, str]] = [
    ("SPOZYWCZE",   r"lidl|biedronka|kaufland|carrefour|auchan|żabka|zabka|tesco|netto"),
    ("RESTAURACJE", r"restauracja|pizza|sushi|kebab|uber.?eats|glovo|wolt|mcdonald|kfc|starbucks"),
    ("TRANSPORT",   r"uber\b|bolt|taxi|orlen|\bbp\b|shell|lotos|circle.?k|pkp|koleo|mzk|ztm|free.?now"),
    ("TELEKOM",     r"orange|t-mobile|tmobile|play\b|plus\b|netia|upc|vectra|inea"),
    ("RACHUNKI",    r"pgnig|tauron|enea|pge\b|energa|innogy|veolia|mpwik|opłata|oplata|czynsz|administracja"),
    ("ROZRYWKA",    r"netflix|spotify|hbo|disney|cinema|kino|cineworld|empik|steam|playstation|xbox"),
    ("PRZELEW_WLASNY", r"przelew własny|przelew wlasny|own transfer|między kontami|miedzy kontami"),
]

_HASH_POOL = ["SPOZYWCZE", "RESTAURACJE", "TRANSPORT", "TELEKOM", "RACHUNKI", "ROZRYWKA", "INNE"]


def _categorize_for_backfill(title: str | None, tx_id: str) -> str:
    if title:
        lower = title.lower()
        for label, pattern in _BACKFILL_RULES:
            if re.search(pattern, lower):
                return label
    digest = hashlib.sha256(tx_id.encode()).digest()
    return _HASH_POOL[digest[0] % len(_HASH_POOL)]


def upgrade() -> None:
    bind = op.get_bind()
    pg_enum = postgresql.ENUM(*_CATEGORY_LABELS, name="transaction_category", create_type=False)
    pg_enum.create(bind, checkfirst=True)

    op.add_column(
        "transactions",
        sa.Column("category", sa.Enum(*_CATEGORY_LABELS, name="transaction_category"), nullable=True),
    )

    rows = bind.execute(sa.text("SELECT id, title FROM transactions")).fetchall()
    for row in rows:
        tx_id = str(row.id)
        category = _categorize_for_backfill(row.title, tx_id)
        bind.execute(
            sa.text("UPDATE transactions SET category = :c WHERE id = :id"),
            {"c": category, "id": row.id},
        )

    with op.batch_alter_table("transactions") as batch:
        batch.alter_column("category", nullable=False, server_default="INNE")


def downgrade() -> None:
    op.drop_column("transactions", "category")
    bind = op.get_bind()
    sa.Enum(name="transaction_category").drop(bind, checkfirst=True)
