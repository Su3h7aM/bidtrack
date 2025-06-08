"""remove_unique_constraint_from_item_code

Revision ID: 3c5b55b7782b
Revises: 992c8bf2ff38
Create Date: 2025-06-06 20:40:06.888051

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3c5b55b7782b"
down_revision: str | None = "6c5c73b24f7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column(
            "code", existing_type=sa.VARCHAR(), nullable=False, unique=False
        )
        batch_op.drop_constraint("uq_item_code", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("item", schema=None) as batch_op:
        batch_op.alter_column(
            "code", existing_type=sa.VARCHAR(), nullable=False, unique=True
        )
        batch_op.create_unique_constraint("uq_item_code", ["code"])
