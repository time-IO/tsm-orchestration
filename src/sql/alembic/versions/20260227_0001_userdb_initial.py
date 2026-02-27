"""initial userdb schema

Revision ID: 20260227_0001
Revises:
Create Date: 2026-02-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260227_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thing",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    op.create_table(
        "journal",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("thing_id", sa.BigInteger(), nullable=False),
        sa.Column("origin", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["thing_id"],
            ["thing.id"],
            deferrable=True,
            initially="DEFERRED",
            name="journal_thing_id_fk_thing_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("journal_thing_id", "journal", ["thing_id"], unique=False)

    op.create_table(
        "datastream",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("position", sa.String(length=200), nullable=False),
        sa.Column("thing_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["thing_id"],
            ["thing.id"],
            deferrable=True,
            initially="DEFERRED",
            name="datastream_thing_id_fk_thing_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thing_id", "position", name="datastream_thing_id_position_uniq"),
    )
    op.create_index("datastream_thing_id", "datastream", ["thing_id"], unique=False)

    op.create_table(
        "observation",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("phenomenon_time_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phenomenon_time_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_type", sa.SmallInteger(), nullable=False),
        sa.Column("result_number", postgresql.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("result_string", sa.String(length=200), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_boolean", sa.Boolean(), nullable=True),
        sa.Column("result_latitude", postgresql.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("result_longitude", postgresql.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("result_altitude", postgresql.DOUBLE_PRECISION(precision=53), nullable=True),
        sa.Column("result_quality", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valid_time_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_time_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("datastream_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["datastream_id"],
            ["datastream.id"],
            deferrable=True,
            initially="DEFERRED",
            name="observation_datastream_id_fk_datastream_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "datastream_id",
            "result_time",
            name="observation_datastream_id_result_time_uniq",
        ),
    )
    op.create_index("idx_observation_result_time", "observation", ["result_time"], unique=False)

    op.create_table(
        "relation_role",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("inverse_name", sa.String(length=200), nullable=False),
        sa.Column("inverse_definition", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name="relation_role_pk"),
        sa.UniqueConstraint("name", name="relation_role_name_uniq"),
        sa.UniqueConstraint("inverse_name", name="relation_role_inverse_name_uniq"),
    )

    op.create_table(
        "related_datastream",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("datastream_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["datastream_id"],
            ["datastream.id"],
            deferrable=True,
            initially="DEFERRED",
            name="related_datastream_datastream_id_fk",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["relation_role.id"],
            deferrable=True,
            initially="DEFERRED",
            name="related_datastream_relation_role_id_fk",
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            ["datastream.id"],
            deferrable=True,
            initially="DEFERRED",
            name="related_datastream_target_id_fk",
        ),
        sa.PrimaryKeyConstraint("id", name="related_datastream_pk"),
        sa.UniqueConstraint(
            "datastream_id",
            "role_id",
            "target_id",
            name="related_datastream_datastream_id_role_id_target_id_uniq",
        ),
    )

    op.create_table(
        "mqtt_message",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("thing_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["thing_id"],
            ["thing.id"],
            deferrable=True,
            initially="DEFERRED",
            name="mqtt_message_thing_id_fk_thing_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO relation_role
                (id, name, definition, inverse_name, inverse_definition, description, properties)
            VALUES
                (1, 'created_by', 'This was created by other(s)', 'created', 'Other(s) created this', 'A derived product', null)
            ON CONFLICT (id) DO UPDATE SET
                name = excluded.name,
                definition = excluded.definition,
                inverse_name = excluded.inverse_name,
                inverse_definition = excluded.inverse_definition,
                description = excluded.description,
                properties = excluded.properties
            """
        )
    )


def downgrade() -> None:
    op.drop_table("mqtt_message")
    op.drop_table("related_datastream")
    op.drop_table("relation_role")
    op.drop_index("idx_observation_result_time", table_name="observation")
    op.drop_table("observation")
    op.drop_index("datastream_thing_id", table_name="datastream")
    op.drop_table("datastream")
    op.drop_index("journal_thing_id", table_name="journal")
    op.drop_table("journal")
    op.drop_table("thing")
