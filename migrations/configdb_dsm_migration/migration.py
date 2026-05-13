import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb, Json

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


def migrate_parsers(cfgdb_cur, dsm_cur, django_things):
    dsm_cur.execute("SELECT id, uuid from public.permission_group")
    projects = dsm_cur.fetchall()
    projects = {p["uuid"]: p["id"] for p in projects}
    cfgdb_cur.execute(queries.GET_PARSER)
    rows = cfgdb_cur.fetchall()
    for row in rows:
        if row["thing_uuid"] in django_things:
            row["project_id"] = projects.get(row["project_uuid"])
            params = row.get("params", {})
            timestamp_columns = params.get("timestamp_columns")
            row["delimiter"] = params.get("delimiter")
            row["skiprows"] = params.get("skiprows")
            row["skipfooter"] = params.get("skipfooter")
            row["pandas_read_csv"] = params.get("pandas_read_csv") or {}
            row["timezone"] = row["pandas_read_csv"].pop("timezone", None)
            row["header"] = row["pandas_read_csv"].pop("header", None)
            row["comment"] = Jsonb(row["pandas_read_csv"].pop("comment", None))
            row["encoding"] = row["pandas_read_csv"].pop("encoding", None)
            adapt_json_fields(row)
            dsm_cur.execute(queries.INSERT_PARSER, row)
            parser_id = dsm_cur.fetchone()["id"]
            row["parser_id"] = parser_id
            dsm_cur.execute(queries.INSERT_PARSER_DETAILED, row)
            dsm_cur.execute(queries.INSERT_PARSER_CSV, row)
            if timestamp_columns:
                for ts in timestamp_columns:
                    dsm_cur.execute(
                        queries.INSERT_PARSER_TS_COLUMNS,
                        {
                            "parser_csv_id": parser_id,
                            "column": ts["column"],
                            "timestamp_format": ts["format"],
                        },
                    )


def adapt_json_fields(row):
    for k, v in row.items():
        if isinstance(v, dict):
            row[k] = Json(v)
    return row


def run_migration(cfgdb_conn, dsm_conn, django_conn):
    try:
        with dsm_conn.transaction():
            cfgdb_cur = cfgdb_conn.cursor()
            dsm_cur = dsm_conn.cursor()
            django_cur = django_conn.cursor()
            django_things = get_django_things(django_cur)
            migrate_project_and_db(cfgdb_cur, dsm_cur)
            migrate_parsers(cfgdb_cur, dsm_cur, django_things)
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
