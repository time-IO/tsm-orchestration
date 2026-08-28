"""add_measurement_key_and_excluded_key_to_parser_json

Revision ID: d404a0156749
Revises: 2987dd5f50bc
Create Date: 2026-08-19 13:11:13.793058

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "d404a0156749"
down_revision: Union[str, Sequence[str], None] = "2987dd5f50bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "parser_json",
        sa.Column("measurement_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "parser_json", sa.Column("excluded_keys", sa.ARRAY(sa.String()), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("parser_json", "excluded_keys")
    op.drop_column("parser_json", "measurement_key")