"""add foreign key ingest/parser/qc_controll setting created_by_id = user.id

Revision ID: e9d8bf38a1c9
Revises: b09bc1ec0794
Create Date: 2026-06-04 10:20:05.756118

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "e9d8bf38a1c9"
down_revision: Union[str, Sequence[str], None] = "b09bc1ec0794"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(None, "parser_detailed", "user", ["created_by_id"], ["id"])
    op.create_foreign_key(None, "ingest", "user", ["created_by_id"], ["id"])
    op.create_foreign_key(
        None, "quality_control_setting", "user", ["created_by_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(None, "parser_detailed", type_="foreignkey")
    op.drop_constraint(None, "ingest", type_="foreignkey")
    op.drop_constraint(None, "quality_control_setting", type_="foreignkey")
