from __future__ import annotations

import re
from pathlib import Path

from alembic import command
from alembic.config import Config
import sqlalchemy as sa

from timeio.alembic.models import Base

LEGACY_BASELINE_REVISION = "20260227_0001"


def _validate_schema_name(schema_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema_name):
        raise ValueError(f"Invalid schema name {schema_name!r}")
    return schema_name


def _convert_url_to_psycopg(database_url: str) -> str:
    """Convert postgresql:// URLs to postgresql+psycopg:// to use psycopg v3."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


def _alembic_config(database_url: str, schema_name: str) -> Config:
    script_location = Path(__file__).resolve().parent
    database_url = _convert_url_to_psycopg(database_url)
    cfg = Config()
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.attributes["target_schema"] = _validate_schema_name(schema_name)
    return cfg


def _schema_has_table(
    connection: sa.Connection, schema_name: str, table_name: str
) -> bool:
    query = sa.text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema_name
              AND table_name = :table_name
        )
        """)
    return bool(
        connection.execute(
            query,
            {"schema_name": schema_name, "table_name": table_name},
        ).scalar()
    )


def upgrade_schema(database_url: str, schema_name: str) -> None:
    cfg = _alembic_config(database_url, schema_name)
    database_url = _convert_url_to_psycopg(database_url)
    engine = sa.create_engine(database_url)
    try:
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            has_thing_table = _schema_has_table(connection, schema_name, "thing")
            has_alembic_table = _schema_has_table(
                connection, schema_name, "alembic_version"
            )
            if has_thing_table and not has_alembic_table:
                command.stamp(cfg, LEGACY_BASELINE_REVISION)
            command.upgrade(cfg, "head")
    finally:
        engine.dispose()


def create_migration(database_url: str, message: str, schema_name: str = "alembic") -> str:
    """Create a new migration revision by comparing models to database.

    Args:
        database_url: Database connection URL
        message: Revision message describing the change
        schema_name: Schema to use for autogenerate comparison (default: "alembic")

    Returns:
        Path to the created migration file
    """
    cfg = _alembic_config(database_url, schema_name)
    database_url = _convert_url_to_psycopg(database_url)
    cfg.attributes["sqlalchemy.url"] = database_url
    cfg.attributes["target_metadata"] = Base.metadata

    # Create the revision with autogenerate enabled
    rev = command.revision(cfg, message=message, autogenerate=True)
    return str(rev.path) if hasattr(rev, "path") else "Migration created"
