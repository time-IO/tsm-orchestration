import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from sql import queries


TABLE_MAP = {
    "ingest_types": ("ingest_type", None),
    "extapi_types": ("ext_api_type", "external_api_type"),
    "mqtt_device_types": ("mqtt_device_type", None),
}


def get_django_things(django_cur):
    django_cur.execute("SELECT thing_id FROM frontenddb.tsm_thing")
    rows = django_cur.fetchall()

    return {r["thing_id"] for r in rows}


def migrate_project_and_db(cfgdb_cur, tmm_cur):
    cfgdb_cur.execute(queries.SELECT_PROJECT_AND_DB)
    rows = cfgdb_cur.fetchall()

    tmm_cur.execute("SELECT uuid, database_id FROM thing_management_db.project")
    existing_projects = {r["uuid"] for r in tmm_cur.fetchall()}

    for row in rows:
        if row["project_uuid"] in existing_projects:
            continue
        row["project_name"] = row["project_name"].split(":")[1]

        tmm_cur.execute(queries.INSERT_DB, row)
        db_id = tmm_cur.fetchone()["id"]
        row["project_database_id"] = db_id
        tmm_cur.execute(queries.INSERT_PROJECT, row)


def migrate_parsers(cfgdb_cur, tmm_cur, django_things):
    tmm_cur.execute("SELECT id, uuid from thing_management_db.project")
    projects = tmm_cur.fetchall()
    projects = {p["uuid"]: p["id"] for p in projects}
    cfgdb_cur.execute(queries.GET_PARSER)
    rows = cfgdb_cur.fetchall()
    valid_rows = []
    for row in rows:
        if row["thing_uuid"] in django_things:
            row["project_id"] = projects.get(row["project_uuid"])
            # hard_coded because only one entry in config_db (csvparser)
            row["file_parser_type_id"] = 1
            # TODO
            row["created_by"] = 1
            adapt_json_fields(row)
            valid_rows.append(row)
    tmm_cur.executemany(queries.INSERT_PARSER, valid_rows)


def map_ids_by_name(cfgdb_cur, tmm_cur, cfgdb_query, tmm_query):
    cfgdb_cur.execute(cfgdb_query)
    tmm_cur.execute(tmm_query)
    cfgdb_rows = cfgdb_cur.fetchall()
    tmm_rows = tmm_cur.fetchall()
    cfgdb_by_name = {row["name"]: row["id"] for row in cfgdb_rows}
    tmm_by_name = {row["name"]: row["id"] for row in tmm_rows}

    return {cfgdb_id: tmm_by_name[name] for name, cfgdb_id in cfgdb_by_name.items()}


def map_table(cfgdb_cur, tmm_cur, cfg_table, tmm_table=None):
    if tmm_table is None:
        tmm_table = cfg_table
    cfg_query = f'SELECT id, "name" FROM config_db.{cfg_table}'
    tmm_query = f'SELECT id, "name" FROM thing_management_db.{tmm_table}'
    return map_ids_by_name(cfgdb_cur, tmm_cur, cfg_query, tmm_query)


def map_type(cfgdb_cur, tmm_cur, key):
    cfg_table, tmm_table = TABLE_MAP[key]
    return map_table(cfgdb_cur, tmm_cur, cfg_table, tmm_table)


def adapt_json_fields(row):
    for k, v in row.items():
        if isinstance(v, dict):
            row[k] = Json(v)
    return row


def migrate_thing_and_ingest(cfgdb_cur, tmm_cur, django_things):
    tmm_cur.execute("SELECT uuid, id FROM thing_management_db.project")
    project_uuid_to_id = {r["uuid"]: r["id"] for r in tmm_cur.fetchall()}

    cfgdb_cur.execute(queries.SELECT_THING_AND_INGEST)
    rows = cfgdb_cur.fetchall()

    tmm_cur.execute('SELECT "uuid", id FROM thing_management_db.file_parser')
    existing_parser = {r["uuid"]: r["id"] for r in tmm_cur.fetchall()}

    ingest_id_mapping = map_type(cfgdb_cur, tmm_cur, "ingest_types")
    extapi_types_mapping = map_type(cfgdb_cur, tmm_cur, "extapi_types")
    mqtt_device_type_mapping = map_type(cfgdb_cur, tmm_cur, "mqtt_device_types")

    for row in rows:
        if row["uuid"] not in django_things:
            continue
        row["project_id"] = project_uuid_to_id[row["project_uuid"]]
        row["ingest_type_id"] = ingest_id_mapping[row["ingest_type_id"]]
        # TODO
        row["created_by"] = 1
        row["ea_api_type_id"] = extapi_types_mapping.get(row["ea_api_type_id"])
        row["mqtt_device_type_id"] = mqtt_device_type_mapping.get(
            row["mqtt_device_type_id"]
        )
        row["file_parser_id"] = existing_parser.get(row["file_parser_uuid"])
        adapt_json_fields(row)
        tmm_cur.execute(queries.UPSERT_THING, row)
        row["thing_id"] = tmm_cur.fetchone()["id"]
        adapt_json_fields(row)
        ingest_name = row["ingest_type_name"]
        upsert_ingest_query = queries.INGEST_QUERIES[ingest_name]
        tmm_cur.execute(upsert_ingest_query, row)


def run_migration(configdb_conn, tmm_conn, django_conn):
    try:
        with tmm_conn.transaction():
            cfgdb_cur = configdb_conn.cursor()
            tmm_cur = tmm_conn.cursor()
            django_cur = django_conn.cursor()
            django_things = get_django_things(django_cur)
            migrate_project_and_db(cfgdb_cur, tmm_cur)
            migrate_parsers(cfgdb_cur, tmm_cur, django_things)
            migrate_thing_and_ingest(cfgdb_cur, tmm_cur, django_things)
    except Exception as e:
        print(f"migration failed: {e}")
        configdb_conn.rollback()
        tmm_conn.rollback()
        django_conn.rollback()
        raise


if __name__ == "__main__":
    # HINTS FOR LOCAL TESTING
    # add respective DSN Entries here for accessing PROD DB!
    # Later we can use the same DSN for cfgdb and tmm. But for testing you can requets PROD config_db schema and write
    # into local thing_management_db schema (same for django DB)
    # currently user_id/created_by  is hardcoded to "1" for thing and parser
    cfgdb_dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    tmm_dsn = "postgresql://postgres:postgres@localhost:5432/postgres"
    django_dsn = "postgresql://frontenddb:frontenddb@localhost:5432/postgres"

    cfgdb_conn = psycopg.connect(cfgdb_dsn, row_factory=dict_row)
    tmm_conn = psycopg.connect(tmm_dsn, row_factory=dict_row)
    django_conn = psycopg.connect(django_dsn, row_factory=dict_row)

    run_migration(cfgdb_conn, tmm_conn, django_conn)
