"""zentraApi

Revision ID: 38995f27c8a8
Revises: d404a0156749
Create Date: 2026-09-28 14:07:02.377751

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "38995f27c8a8"
down_revision: Union[str, Sequence[str], None] = "d404a0156749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingest_external_api_zentra",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column("device_sn", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("period_in_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "units", sa.Enum("METRIC", "IMPERIAL", name="unitsenum"), nullable=True
        ),
        sa.Column("api_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_mrid", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(
            ["ingest_id"], ["ingest_external_api.ingest_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("ingest_id"),
    )

    op.drop_constraint("ck_api_type", "ingest_external_api", type_="check")
    op.create_check_constraint(
        "ck_api_type",
        "ingest_external_api",
        "api_type IN ('bosch', 'dwd', 'nm', 'ttn', 'tsystems', 'uba', 'sensoto', 'zentra')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ingest_external_api_zentra")
    op.execute("DROP TYPE IF EXISTS unitsenum")
    op.drop_constraint("ck_api_type", "ingest_external_api", type_="check")
    op.create_check_constraint(
        "ck_api_type",
        "ingest_external_api",
        "api_type IN ('bosch', 'dwd', 'nm', 'ttn', 'tsystems', 'uba', 'sensoto')",
    )