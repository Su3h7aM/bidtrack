"""update_item_model

Revision ID: 6c5c73b24f7d
Revises: manual_001_add_link_to_quote
Create Date: 2025-06-06 17:06:40.397126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c5c73b24f7d'
down_revision: Union[str, None] = 'manual_001_add_link_to_quote'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column('name', existing_type=sa.VARCHAR(), unique=False)
        batch_op.alter_column('code', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.create_unique_constraint('uq_item_code', ['code'])
        batch_op.alter_column('unit', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.add_column(sa.Column('notes', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column('name', existing_type=sa.VARCHAR(), unique=True)
        batch_op.drop_constraint('uq_item_code', type_='unique')
        batch_op.alter_column('code', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column('unit', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.drop_column('notes')
