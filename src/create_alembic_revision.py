#!/usr/bin/env python3
"""Create a new Alembic migration revision.

Usage:
    create_alembic_revision.py <message>

Environment variables:
    DATABASE_URL: Database connection URL (required)
    ALEMBIC_SCHEMA: Schema to use for autogenerate comparison (optional, default: "alembic")

Example:
    export DATABASE_URL="postgresql+psycopg://user:pass@localhost/db"
    ./create_alembic_revision.py "add column foo to datastream"
"""

from __future__ import annotations

import os
import sys

from timeio.alembic.runner import create_migration
from timeio.common import get_envvar


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    message = " ".join(sys.argv[1:])
    database_url = get_envvar("DATABASE_URL")
    schema_name = os.environ.get("ALEMBIC_SCHEMA", "vo_demogroup_887a7030491444e0aee126fbc215e9f7")

    try:
        result = create_migration(database_url, message, schema_name)
        print(f"✓ Migration created: {result}")
        return 0
    except Exception as e:
        print(f"✗ Failed to create migration: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
