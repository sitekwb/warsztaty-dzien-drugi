"""v3 phase 5b: transactions dual approval columns

Revision ID: 85ad02d8da7a
Revises: 067db81ef933
Create Date: 2026-05-26 12:40:36.679506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import minibank.db.models


# revision identifiers, used by Alembic.
revision: str = '85ad02d8da7a'
down_revision: Union[str, Sequence[str], None] = '067db81ef933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('requires_dual_approval', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('approved_by_user_id', minibank.db.models.GUID(), nullable=True))
        batch_op.create_foreign_key('fk_transactions_approved_by_user_id', 'users', ['approved_by_user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_constraint('fk_transactions_approved_by_user_id', type_='foreignkey')
        batch_op.drop_column('approved_by_user_id')
        batch_op.drop_column('requires_dual_approval')
