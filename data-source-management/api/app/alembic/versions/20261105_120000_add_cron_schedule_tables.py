"""add_cron_schedule_tables

Revision ID: 5c1e7a9d3b42
Revises: 38995f27c8a8
Create Date: 2026-11-05 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5c1e7a9d3b42"
down_revision: Union[str, Sequence[str], None] = "38995f27c8a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingest_schedule",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column(
            "cron_expression", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("jitter_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_ingest_schedule_jitter"
        ),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ingest_id"),
    )
    op.create_table(
        "custom_job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ingest_id", sa.Integer(), nullable=True),
        sa.Column("permission_group_id", sa.Integer(), nullable=True),
        sa.Column(
            "params",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "cron_expression", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("jitter_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "job_type IN ('sync_thing', 'resync_thing', 'resync_project', 'sync_sms')",
            name="ck_custom_job_type",
        ),
        sa.CheckConstraint(
            "(job_type IN ('sync_thing', 'resync_thing')) = (ingest_id IS NOT NULL)",
            name="ck_custom_job_ingest",
        ),
        sa.CheckConstraint(
            "(job_type = 'resync_project') = (permission_group_id IS NOT NULL)",
            name="ck_custom_job_permission_group",
        ),
        sa.CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_custom_job_jitter"
        ),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["permission_group_id"], ["permission_group.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("custom_job")
    op.drop_table("ingest_schedule")
