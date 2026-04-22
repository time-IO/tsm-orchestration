import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from sql import queries


def get_django_things(django_cur):
    django_cur.execute("SELECT thing_id FROM frontenddb.tsm_thing")
    rows = django_cur.fetchall()

    return {r["thing_id"] for r in rows}


def migrate_project_and_db(cfgdb_cur, dsm_cur):
    cfgdb_cur.execute(queries.SELECT_PROJECT_AND_DB)
    rows = cfgdb_cur.fetchall()

    dsm_cur.execute("SELECT uuid FROM public.permission_group")
    existing_projects = {r["uuid"] for r in dsm_cur.fetchall()}

    for row in rows:
        if row["project_uuid"] in existing_projects:
            continue
        row["project_name"] = row["project_name"].split(":")[1]

        dsm_cur.execute(queries.INSERT_PROJECT, row)
        project_id = dsm_cur.fetchone()["id"]
        row["project_id"] = project_id
        dsm_cur.execute(queries.INSERT_DB, row)


def run_migration(cfgdb_conn, dsm_conn, django_conn):
    try:
        with dsm_conn.transaction():
            cfgdb_cur = cfgdb_conn.cursor()
            dsm_cur = dsm_conn.cursor()
            django_cur = django_conn.cursor()
            migrate_project_and_db(cfgdb_cur, dsm_cur)
    except Exception as e:
        print(f"migration failed: {e}")
        cfgdb_conn.rollback()
        tmm_conn.rollback()
        django_conn.rollback()
        raise


if __name__ == "__main__":
    cfgdb_dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    tmm_dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    django_dsn = "postgresql://frontenddb:frontenddb@localhost:5432/postgres"

    cfgdb_conn = psycopg.connect(cfgdb_dsn, row_factory=dict_row)
    tmm_conn = psycopg.connect(tmm_dsn, row_factory=dict_row)
    django_conn = psycopg.connect(django_dsn, row_factory=dict_row)

    run_migration(cfgdb_conn, tmm_conn, django_conn)
