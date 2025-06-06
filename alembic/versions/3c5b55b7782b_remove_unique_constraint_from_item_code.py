"""remove_unique_constraint_from_item_code

Revision ID: 3c5b55b7782b
Revises: 992c8bf2ff38
Create Date: 2025-06-06 20:40:06.888051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c5b55b7782b'
down_revision: Union[str, None] = '6c5c73b24f7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('uq_item_code', 'item', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint('uq_item_code', 'item', ['code'])
