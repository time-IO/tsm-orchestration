"""add-quaesta-mqtt-parser

Revision ID: 99c357d1b3b3
Revises: d97c6055955e
Create Date: 2026-06-26 09:24:49.995113

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import uuid as uuid_pkg

# revision identifiers, used by Alembic.
revision: str = "99c357d1b3b3"
down_revision: Union[str, Sequence[str], None] = "d97c6055955e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

parser = sa.table(
    "parser",
    sa.column("id", sa.Integer),
    sa.column("uuid", sa.Uuid),
    sa.column("parser_type", sa.String),
)

parser_mqtt = sa.table(
    "parser_mqtt",
    sa.column("parser_id", sa.Integer),
    sa.column("name", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""

    result = op.get_bind().execute(
        sa.insert(parser)
        .values(
            uuid=uuid_pkg.UUID("d85a8b54-57fe-423b-abba-72721364c648"),
            parser_type="mqtt",
        )
        .returning(parser.c.id)
    )

    parser_id = result.scalar_one()

    op.bulk_insert(
        parser_mqtt,
        [
            {
                "parser_id": parser_id,
                "name": "quaesta",
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM parser_mqtt, parser WHERE parser.uuid = 'd85a8b54-57fe-423b-abba-72721364c648' AND parser_mqtt.parser_id = parser.id"
    )
    op.execute("DELETE FROM parser WHERE uuid = 'd85a8b54-57fe-423b-abba-72721364c648'")
