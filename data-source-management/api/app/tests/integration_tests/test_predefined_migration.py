"""Exercise upgrade and downgrade against an isolated legacy-schema fixture."""

import importlib.util
from pathlib import Path
import uuid

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from dependencies import engine


def test_predefined_migration_preserves_records_and_references():
    path = (
        Path(__file__).parents[2]
        / "alembic/versions/20261111_100000_unify_predefined_parsers.py"
    )
    spec = importlib.util.spec_from_file_location("predefined_revision", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    schema = "migration_test_" + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
        conn.execute(sa.text(f'SET LOCAL search_path TO "{schema}"'))
        conn.execute(sa.text("""CREATE TABLE parser (
            id SERIAL PRIMARY KEY, uuid UUID NOT NULL UNIQUE, parser_type TEXT NOT NULL,
            CONSTRAINT ck_parser_type CHECK (parser_type IN ('csv','json','mqtt','soilcan'))
        )"""))
        conn.execute(
            sa.text(
                "CREATE TABLE parser_mqtt (parser_id INTEGER PRIMARY KEY REFERENCES parser(id), name TEXT NOT NULL)"
            )
        )
        conn.execute(
            sa.text(
                "CREATE TABLE ingest (id INTEGER PRIMARY KEY, parser_id INTEGER REFERENCES parser(id))"
            )
        )
        mqtt_uuid = uuid.uuid4()
        conn.execute(
            sa.text("INSERT INTO parser (uuid, parser_type) VALUES (:uuid, 'mqtt')"),
            {"uuid": mqtt_uuid},
        )
        conn.execute(sa.text("INSERT INTO parser_mqtt VALUES (1, 'campbell_cr6')"))
        conn.execute(sa.text("INSERT INTO ingest VALUES (1, 1)"))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            assert conn.execute(
                sa.text("SELECT uuid, parser_type FROM parser WHERE id = 1")
            ).one() == (mqtt_uuid, "predefined")
            assert (
                conn.execute(
                    sa.text("SELECT parser_id FROM ingest WHERE id = 1")
                ).scalar_one()
                == 1
            )
            assert (
                conn.execute(
                    sa.text("SELECT name FROM parser_predefined WHERE parser_id = 1")
                ).scalar_one()
                == "campbell_cr6"
            )
            true_id = conn.execute(
                sa.text(
                    "SELECT parser_id FROM parser_predefined WHERE name = 'truelog100'"
                )
            ).scalar_one()
            conn.execute(sa.text("INSERT INTO ingest VALUES (2, :id)"), {"id": true_id})
            # A downgrade must not silently discard a saved TrueLog100 selection.
            with pytest.raises(sa.exc.IntegrityError):
                with conn.begin_nested():
                    migration.downgrade()
            assert (
                conn.execute(
                    sa.text("SELECT parser_id FROM ingest WHERE id = 2")
                ).scalar_one()
                == true_id
            )
            conn.execute(sa.text("DELETE FROM ingest WHERE id = 2"))
            migration.downgrade()
            assert conn.execute(
                sa.text("SELECT uuid, parser_type FROM parser WHERE id = 1")
            ).one() == (mqtt_uuid, "mqtt")
            assert (
                conn.execute(
                    sa.text("SELECT name FROM parser_mqtt WHERE parser_id = 1")
                ).scalar_one()
                == "campbell_cr6"
            )
            migration.upgrade()
            assert (
                conn.execute(
                    sa.text(
                        "SELECT count(*) FROM parser_predefined WHERE name = 'truelog100'"
                    )
                ).scalar_one()
                == 1
            )
        conn.execute(sa.text("SET LOCAL search_path TO public"))
        conn.execute(sa.text(f'DROP SCHEMA "{schema}" CASCADE'))
