"""Rename MQTT metadata to predefined parsers and seed TrueLog100.

Revision ID: b71df45e920a
Revises: 38995f27c8a8
"""

import uuid

from alembic import op
import sqlalchemy as sa

revision = "b71df45e920a"
down_revision = "38995f27c8a8"
branch_labels = None
depends_on = None

TRUELOG_UUID = uuid.UUID("9e9b220d-c977-4f6f-a4e2-bbe3f6b72817")
parser = sa.table(
    "parser",
    sa.column("id", sa.Integer),
    sa.column("uuid", sa.Uuid),
    sa.column("parser_type", sa.String),
)
predefined = sa.table(
    "parser_predefined",
    sa.column("parser_id", sa.Integer),
    sa.column("name", sa.String),
)


def upgrade() -> None:
    # Rename in place to retain every MQTT parser ID, UUID and ingest reference.
    op.rename_table("parser_mqtt", "parser_predefined")
    op.drop_constraint("ck_parser_type", "parser", type_="check")
    op.execute(
        sa.update(parser)
        .where(parser.c.parser_type == "mqtt")
        .values(parser_type="predefined")
    )
    op.create_check_constraint(
        "ck_parser_type",
        "parser",
        "parser_type IN ('csv','json','predefined','soilcan')",
    )
    parser_id = (
        op.get_bind()
        .execute(
            sa.insert(parser)
            .values(uuid=TRUELOG_UUID, parser_type="predefined")
            .returning(parser.c.id)
        )
        .scalar_one()
    )
    op.bulk_insert(predefined, [{"parser_id": parser_id, "name": "truelog100"}])


def downgrade() -> None:
    # An ingest referencing TrueLog100 must be reassigned first. Its FK blocks
    # removal and PostgreSQL rolls back this migration rather than losing data.
    op.execute(
        sa.delete(predefined).where(
            predefined.c.parser_id.in_(
                sa.select(parser.c.id).where(parser.c.uuid == TRUELOG_UUID)
            )
        )
    )
    op.execute(sa.delete(parser).where(parser.c.uuid == TRUELOG_UUID))
    op.drop_constraint("ck_parser_type", "parser", type_="check")
    op.execute(
        sa.update(parser)
        .where(parser.c.parser_type == "predefined")
        .values(parser_type="mqtt")
    )
    op.create_check_constraint(
        "ck_parser_type", "parser", "parser_type IN ('csv','json','mqtt','soilcan')"
    )
    op.rename_table("parser_predefined", "parser_mqtt")
