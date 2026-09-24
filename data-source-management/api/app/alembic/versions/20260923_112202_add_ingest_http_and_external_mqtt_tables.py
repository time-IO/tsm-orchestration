"""add ingest http and external mqtt tables, with http bucket credentials

Revision ID: 4e4465cdc4ba
Revises: d404a0156749
Create Date: 2026-09-23 11:22:02.413136

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from encryption import EncryptedType

# revision identifiers, used by Alembic.
revision: str = "4e4465cdc4ba"
down_revision: Union[str, Sequence[str], None] = "d404a0156749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingest_external_mqtt",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column(
            "external_mqtt_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("external_mqtt_port", sa.Integer(), nullable=False),
        sa.Column(
            "external_mqtt_username", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("external_mqtt_password", EncryptedType(), nullable=True),
        sa.Column("external_mqtt_ca_cert", EncryptedType(), nullable=True),
        sa.Column("external_mqtt_client_cert", EncryptedType(), nullable=True),
        sa.Column("external_mqtt_client_key", EncryptedType(), nullable=True),
        sa.Column(
            "external_mqtt_topic", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ingest_id"),
    )
    op.create_table(
        "ingest_http",
        sa.Column("ingest_id", sa.Integer(), nullable=False),
        sa.Column("path_for_posts", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("file_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("api_key", EncryptedType(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("bucket_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "bucket_username", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("bucket_password", EncryptedType(), nullable=False),
        sa.ForeignKeyConstraint(["ingest_id"], ["ingest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ingest_id"),
    )
    # path_for_posts feeds the global Bento HTTP route (/http-ingest/{path}),
    # so it must be unique instance-wide. NULL is excluded: setup_bento.py
    # falls back to the thing's UUID (already unique) when no path is set.
    op.create_index(
        "ix_ingest_http_path_for_posts",
        "ingest_http",
        ["path_for_posts"],
        unique=True,
        postgresql_where=sa.text("path_for_posts IS NOT NULL"),
    )
    op.drop_constraint("ck_ingest_type", "ingest", type_="check")
    op.create_check_constraint(
        "ck_ingest_type",
        "ingest",
        "ingest_type IN ('mqtt','sftp','external_api', 'external_sftp', 'external_mqtt', 'http')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_ingest_type", "ingest", type_="check")
    op.create_check_constraint(
        "ck_ingest_type",
        "ingest",
        "ingest_type IN ('mqtt','sftp','external_api', 'external_sftp')",
    )
    op.drop_index("ix_ingest_http_path_for_posts", table_name="ingest_http")
    op.drop_table("ingest_http")
    op.drop_table("ingest_external_mqtt")
