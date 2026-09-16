"""add_position_to_quality_control_function

Revision ID: 72352b0b8990
Revises: d404a0156749
Create Date: 2026-08-26 15:05:13.442299

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "72352b0b8990"
down_revision: Union[str, Sequence[str], None] = "d404a0156749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "quality_control_function",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        """
        UPDATE quality_control_function AS qcf
        SET position = sub.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY quality_control_setting_id ORDER BY id
            ) - 1 AS rn
            FROM quality_control_function
        ) AS sub
        WHERE qcf.id = sub.id
        """
    )
    op.alter_column("quality_control_function", "position", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("quality_control_function", "position")