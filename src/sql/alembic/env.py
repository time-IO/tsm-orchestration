from __future__ import annotations

import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from timeio.alembic.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_target_schema() -> str:
    schema = config.attributes.get("target_schema")
    if not schema:
        x_args = context.get_x_argument(as_dictionary=True)
        schema = x_args.get("schema")
    if not schema:
        raise ValueError("Missing target schema for migration run")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Invalid target schema {schema!r}")
    return schema


def run_migrations_offline() -> None:
    target_schema = _get_target_schema()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=target_schema,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    target_schema = _get_target_schema()

    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    if hasattr(connectable, "connect"):
        with connectable.connect() as connection:
            connection.execute(text(f'SET search_path TO "{target_schema}", public'))
            connection.dialect.default_schema_name = target_schema
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table_schema=target_schema,
                compare_type=True,
                compare_server_default=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    else:
        connection = connectable
        connection.execute(text(f'SET search_path TO "{target_schema}", public'))
        connection.dialect.default_schema_name = target_schema
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_schema,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
