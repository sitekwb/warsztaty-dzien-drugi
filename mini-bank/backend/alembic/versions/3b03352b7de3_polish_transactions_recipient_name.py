"""polish: transactions.recipient_name

Revision ID: 3b03352b7de3
Revises: 85ad02d8da7a
Create Date: 2026-05-27 10:38:28.751179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b03352b7de3'
down_revision: Union[str, Sequence[str], None] = '85ad02d8da7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add as nullable first so we can backfill historical rows.
    op.add_column("transactions", sa.Column("recipient_name", sa.String(length=140), nullable=True))
    # Backfill seed-generated rows.
    op.execute("UPDATE transactions SET recipient_name = 'Brak nazwy' WHERE recipient_name IS NULL")
    # Now enforce NOT NULL.
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column("recipient_name", existing_type=sa.String(length=140), nullable=False)


def downgrade() -> None:
    op.drop_column("transactions", "recipient_name")
