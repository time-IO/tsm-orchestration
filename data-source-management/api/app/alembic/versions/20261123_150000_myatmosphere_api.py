"""myatmosphere api

Revision ID: 5069b8594760
Revises: b71df45e920a
Create Date: 2026-11-23 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "5069b8594760"
down_revision: Union[str, Sequence[str], None] = "b71df45e920a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingest_external_api_myatmosphere",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("serial_number", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("period_in_minutes", sa.Integer(), nullable=False),
        sa.Column("api_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingest_id"], ["ingest_external_api.ingest_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("ingest_id"),
    )

    op.drop_constraint("ck_api_type", "ingest_external_api", type_="check")
    op.create_check_constraint(
        "ck_api_type",
        "ingest_external_api",
        "api_type IN ('bosch', 'dwd', 'nm', 'ttn', 'tsystems', 'uba', 'sensoto', 'zentra', 'myatmosphere')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ingest_external_api_myatmosphere")
    op.drop_constraint("ck_api_type", "ingest_external_api", type_="check")
    op.create_check_constraint(
        "ck_api_type",
        "ingest_external_api",
        "api_type IN ('bosch', 'dwd', 'nm', 'ttn', 'tsystems', 'uba', 'sensoto', 'zentra')",
    )
