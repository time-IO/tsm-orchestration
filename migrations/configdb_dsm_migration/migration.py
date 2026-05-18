import uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb, Json

from sql import queries


def get_django_things(django_cur):
    django_cur.execute("SELECT thing_id FROM frontenddb.tsm_thing")
    rows = django_cur.fetchall()

    return {r["thing_id"] for r in rows}


def get_django_qc(django_cur):
    django_cur.execute("""SELECT "name" FROM frontenddb.tsm_qaqcsetting""")
    rows = django_cur.fetchall()

    return {r["name"] for r in rows}


def get_existing_dsm_projects(dsm_cur):
    dsm_cur.execute("SELECT id, uuid from dsm_db.permission_group")
    projects = dsm_cur.fetchall()
    projects = {p["uuid"]: p["id"] for p in projects}

    return projects


def migrate_project_and_db(cfgdb_cur, dsm_cur):
    cfgdb_cur.execute(queries.SELECT_PROJECT_AND_DB)
    rows = cfgdb_cur.fetchall()

    dsm_cur.execute("SELECT uuid FROM dsm_db.permission_group")
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
    projects = get_existing_dsm_projects(dsm_cur)
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


def migrate_ingests(cfgdb_cur, dsm_cur, django_things):
    projects = get_existing_dsm_projects(dsm_cur)
    dsm_cur.execute("SELECT id, uuid from dsm_db.parser")
    parser = dsm_cur.fetchall()
    parser = {p["uuid"]: p["id"] for p in parser}
    cfgdb_cur.execute(queries.SELECT_THING_AND_INGEST)
    rows = cfgdb_cur.fetchall()
    for row in rows:
        if row["thing_uuid"] not in django_things:
            continue
        row["project_id"] = projects[row["project_uuid"]]
        file_parser_uuid = row["file_parser_uuid"]
        row["parser_id"] = (
            parser[file_parser_uuid] if file_parser_uuid is not None else None
        )
        if row["ingest_type_name"] == "extapi":
            row["ingest_type_name"] = "external_api"
        if row["ingest_type_name"] == "extsftp":
            row["ingest_type_name"] = "external_sftp"
        dsm_cur.execute(queries.INSERT_INGEST, row)
        row["ingest_id"] = dsm_cur.fetchone()["id"]
        if row["ingest_type_name"] == "sftp":
            dsm_cur.execute(queries.INSERT_INGEST_SFTP, row)
        if row["ingest_type_name"] == "external_sftp":
            dsm_cur.execute(queries.INSERT_INGEST_EXT_SFTP, row)
        if row["ingest_type_name"] == "external_api":
            dsm_cur.execute(queries.INSERT_INGEST_EXT_API, row)
            if row["ea_type_name"] == "ttn":
                row["ttn_api_key"] = row["ea_settings"].get("api_key")
                row["ttn_uri"] = row["ea_settings"].get("endpoint_uri")
                dsm_cur.execute(queries.INSERT_INGEST_TTN_API, row)
            if row["ea_type_name"] == "dwd":
                row["dwd_station_id"] = row["ea_settings"].get("station_id")
                row["dwd_period"] = row["ea_settings"].get("period")
                dsm_cur.execute(queries.INSERT_INGEST_DWD_API, row)
            if row["ea_type_name"] == "nm":
                # currently no things with ext_api = Neutronenmonitor in configdb
                pass
            if row["ea_type_name"] == "bosch":
                row["bosch_sensor"] = row["ea_settings"].get("sensor_id")
                row["bosch_user"] = row["ea_settings"].get("username")
                row["bosch_password"] = row["ea_settings"].get("password")
                row["bosch_endpoint"] = row["ea_settings"].get("endpoint")
                row["bosch_period"] = row["ea_settings"].get("period")
                dsm_cur.execute(queries.INSERT_INGEST_BOSCH_API, row)
            if row["ea_type_name"] == "tsystems":
                row["tsystems_group"] = row["ea_settings"].get("group")
                row["tsystems_station"] = row["ea_settings"].get("station_id")
                row["tsystems_password"] = row["ea_settings"].get("password")
                row["tsystems_username"] = row["ea_settings"].get("username")
                dsm_cur.execute(queries.INSERT_INGEST_TSYSTEMS_API, row)
            if row["ea_type_name"] == "uba":
                row["uba_station_id"] = row["ea_settings"].get("station_id")
                dsm_cur.execute(queries.INSERT_INGEST_UBA_API, row)


def adapt_json_fields(row):
    for k, v in row.items():
        if isinstance(v, dict):
            row[k] = Json(v)
    return row


def migrate_qc(cfgdb_cur, dsm_cur, django_qc):
    projects = get_existing_dsm_projects(dsm_cur)
    cfgdb_cur.execute(queries.SELECT_QAQC)
    rows = cfgdb_cur.fetchall()
    for row in rows:
        if row["qc_name"] not in django_qc:
            continue
        row["project_id"] = projects[row["project_uuid"]]
        row["qc_uuid"] = uuid.uuid5(uuid.NAMESPACE_DNS, f"{row["id"]}")
        dsm_cur.execute(queries.INSERT_QC_SETTINGS, row)


def run_migration(cfgdb_conn, dsm_conn, django_conn):
    try:
        with dsm_conn.transaction():
            cfgdb_cur = cfgdb_conn.cursor()
            dsm_cur = dsm_conn.cursor()
            django_cur = django_conn.cursor()
            django_things = get_django_things(django_cur)
            django_qc = get_django_qc(django_cur)
            migrate_project_and_db(cfgdb_cur, dsm_cur)
            migrate_parsers(cfgdb_cur, dsm_cur, django_things)
            migrate_ingests(cfgdb_cur, dsm_cur, django_things)
            migrate_qc(cfgdb_cur, dsm_cur, django_qc)
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
