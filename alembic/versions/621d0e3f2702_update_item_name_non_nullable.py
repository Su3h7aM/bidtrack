"""update_item_name_non_nullable

Revision ID: 621d0e3f2702
Revises: 3c5b55b7782b
Create Date: 2025-06-06 23:39:56.366812

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Keep sqlmodel import if it was there, good practice


# revision identifiers, used by Alembic.
revision: str = "621d0e3f2702"
down_revision: Union[str, None] = "3c5b55b7782b"  # Confirmed this is correct
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.drop_constraint("uq_item_name", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(), nullable=True)
        batch_op.create_unique_constraint("uq_item_name", ["name"])
