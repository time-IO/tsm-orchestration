"""add_label_to_quality_control_function

Revision ID: 5f1bce7c9a83
Revises: 2987dd5f50bc
Create Date: 2026-08-25 08:06:08.669546

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "5f1bce7c9a83"
down_revision: Union[str, Sequence[str], None] = "2987dd5f50bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "quality_control_function",
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("quality_control_function", "label")
