"""add_cron_schedule_tables

Revision ID: 5c1e7a9d3b42
Revises: b71df45e920a
Create Date: 2026-11-05 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5c1e7a9d3b42"
down_revision: Union[str, Sequence[str], None] = "b71df45e920a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingest_schedule",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column("cron_expression", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("jitter_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_ingest_schedule_jitter"
        ),
        sa.CheckConstraint(
            "NOT enabled OR cron_expression IS NOT NULL",
            name="ck_ingest_schedule_expression",
        ),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ingest_id"),
    )
    op.create_table(
        "scheduled_job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ingest_id", sa.Integer(), nullable=True),
        sa.Column("quality_control_setting_id", sa.Integer(), nullable=True),
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
            "job_type IN ('resync_thing', 'sync_sms', 'mqtt_monitoring', 'trigger_qc')",
            name="ck_scheduled_job_type",
        ),
        sa.CheckConstraint(
            "(job_type = 'resync_thing') = (ingest_id IS NOT NULL)",
            name="ck_scheduled_job_ingest",
        ),
        sa.CheckConstraint(
            "(job_type = 'trigger_qc') = (quality_control_setting_id IS NOT NULL)",
            name="ck_scheduled_job_qc_setting",
        ),
        sa.CheckConstraint(
            "jitter_seconds BETWEEN 0 AND 59", name="ck_scheduled_job_jitter"
        ),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["quality_control_setting_id"],
            ["quality_control_setting.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("scheduled_job")
    op.drop_table("ingest_schedule")
