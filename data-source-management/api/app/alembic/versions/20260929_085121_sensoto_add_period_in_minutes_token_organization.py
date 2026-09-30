"""add period_in_minutes to sensoto

Revision ID: 7573ab5032f3
Revises: d404a0156749
Create Date: 2026-09-29 08:51:21.721077

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "7573ab5032f3"
down_revision: Union[str, Sequence[str], None] = "d404a0156749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ingest_external_api_sensoto",
        sa.Column(
            "period_in_minutes", sa.Integer(), nullable=False, server_default="60"
        ),
    )
    op.alter_column(
        "ingest_external_api_sensoto", "period_in_minutes", server_default=None
    )
    op.add_column(
        "ingest_external_api_sensoto",
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "ingest_external_api_sensoto",
        sa.Column(
            "organization",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="open",
        ),
    )
    op.alter_column("ingest_external_api_sensoto", "organization", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ingest_external_api_sensoto", "organization")
    op.drop_column("ingest_external_api_sensoto", "token")
    op.drop_column("ingest_external_api_sensoto", "period_in_minutes")
