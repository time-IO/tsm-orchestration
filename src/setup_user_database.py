from __future__ import annotations

import json
import logging
import os
import re

import psycopg
from psycopg import sql
from typing import cast, Literal

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.databases import Database
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.journaling import Journal
from timeio.crypto import decrypt, get_crypt_key

logger = logging.getLogger("db-setup")
journal = Journal("System", errors="ignore")

STA_PREFIX = "sta_"
GRF_PREFIX = "grf_"
STI_PREFIX = "sti_"
# Suffix for the per-project schema that holds the "internal" FROST views
# (public + internal visibility). Served by a separate, non-proxied FROST.
INTERNAL_SUFFIX = "_internal"


class CreateThingInPostgresHandler(AbstractHandler):
    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        self.db = Database(get_envvar("DATABASE_URL"))
        self.dsmdb_dsn = get_envvar("DSMDB_DSN")

    def act(self, content: dict, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.dsmdb_dsn)
        logger.info(f"start processing. {thing.name=}, {thing.uuid=}")
        ro_user = thing.database.ro_username.lower()
        user = thing.database.username.lower()

        # 1. Check, if there is already a database user for this project
        if not self.user_exists(user):
            logger.debug(f"create user {user}")
            self.create_user(thing)
            logger.debug("create schema")
            self.create_schema(thing)
            logger.debug("deploy dll")
            self.deploy_ddl(thing)
            logger.debug("deploy dml")
            self.deploy_dml(thing)

        if not self.user_exists(sta_user := STA_PREFIX + ro_user):
            logger.debug(f"create sta read-only user {sta_user}")
            self.create_ro_user(thing, user_prefix=STA_PREFIX)

        if not self.user_exists(grf_user := GRF_PREFIX + ro_user):
            logger.debug(f"create grafana read-only user {grf_user}")
            self.create_ro_user(thing, user_prefix=GRF_PREFIX)

        if not self.user_exists(sti_user := STI_PREFIX + ro_user):
            logger.debug(f"create sta-internal read-only user {sti_user}")
            self.create_internal_schema(thing)
            self.create_ro_user(
                thing, user_prefix=STI_PREFIX, schema=user + INTERNAL_SUFFIX
            )

        logger.info("update/create thing in db")
        created = self.upsert_thing(thing)
        journal.info(f"{'Created' if created else 'Updated'} Thing", thing.uuid)

        logger.debug("create/refresh frost views")
        self.create_frost_views(thing)
        logger.debug(f"grand frost view privileges to {sta_user}")
        self.grant_sta_select(thing, user_prefix=STA_PREFIX)
        logger.debug("create/refresh internal frost views")
        self.create_frost_views(thing, internal=True)
        logger.debug(f"grant internal frost view privileges to {sti_user}")
        self.grant_sta_select(
            thing, user_prefix=STI_PREFIX, schema=user + INTERNAL_SUFFIX
        )
        logger.debug("create/refresh grafana views")
        self.create_grafana_views(thing)
        logger.debug(f"grand grafana view privileges to {grf_user}")
        self.grant_grafana_select(thing, user_prefix=GRF_PREFIX)

        self.upsert_schema_thing_mapping(thing)

    def create_user(self, thing):

        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                passw = decrypt(thing.database.password, get_crypt_key())
                c.execute(
                    sql.SQL("CREATE ROLE {user} WITH LOGIN PASSWORD {password}").format(
                        user=user, password=sql.Literal(passw)
                    )
                )
                c.execute(
                    sql.SQL("GRANT {user} TO {creator}").format(
                        user=user, creator=sql.Identifier(conn.info.user)
                    )
                )

    def create_ro_user(self, thing, user_prefix: str = "", schema: str | None = None):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                ro_username = user_prefix.lower() + thing.database.ro_username.lower()
                ro_user = sql.Identifier(ro_username)
                schema = sql.Identifier(schema or thing.database.username.lower())
                ro_passw = decrypt(thing.database.ro_password, get_crypt_key())

                c.execute(
                    sql.SQL(
                        "CREATE ROLE {ro_user} WITH LOGIN PASSWORD {ro_password}"
                    ).format(ro_user=ro_user, ro_password=sql.Literal(ro_passw))
                )

                c.execute(
                    sql.SQL("GRANT {ro_user} TO {creator}").format(
                        ro_user=ro_user, creator=sql.Identifier(conn.info.user)
                    )
                )

                # Allow tcp connections to database with new user
                c.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {db_name} TO {ro_user}").format(
                        ro_user=ro_user, db_name=sql.Identifier(conn.info.dbname)
                    )
                )

                c.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {schema} TO {ro_user}").format(
                        ro_user=ro_user, schema=schema
                    )
                )

    def password_has_changed(self, url, user, password):
        try:
            with psycopg.connect(url, user=user, password=password):
                pass
        except psycopg.OperationalError as e:
            if "password authentication failed" in str(e):
                return True
            raise e
        else:
            return False

    def maybe_update_password(self, user, password, db_url):
        # NOTE: currently unused function
        password = decrypt(password, get_crypt_key())
        if not self.password_has_changed(user, password, db_url):
            return

        logger.debug(f"update password for user {user}")
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    sql.SQL("ALTER USER {user} WITH PASSWORD {password}").format(
                        user=sql.Identifier(user), password=sql.Identifier(password)
                    )
                )

    def create_schema(self, thing):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    sql.SQL(
                        "CREATE SCHEMA IF NOT EXISTS {user} AUTHORIZATION {user}"
                    ).format(user=sql.Identifier(thing.database.username.lower()))
                )

    def create_internal_schema(self, thing):
        # Separate schema holding the "internal" FROST views, owned by the
        # project user (same as the public schema).
        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                c.execute(
                    sql.SQL(
                        "CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}"
                    ).format(
                        schema=sql.Identifier(
                            thing.database.username.lower() + INTERNAL_SUFFIX
                        ),
                        user=user,
                    )
                )

    def deploy_ddl(self, thing):
        file = os.path.join(os.path.dirname(__file__), "sql", "postgres-ddl.sql")
        with open(file) as fh:
            query = fh.read()

        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                # Set search path for current session
                c.execute(sql.SQL("SET search_path TO {0}").format(user))
                # Allow tcp connections to database with new user
                c.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {db_name} TO {user}").format(
                        user=user, db_name=sql.Identifier(conn.info.dbname)
                    )
                )
                # Set default schema when connecting as user
                c.execute(
                    sql.SQL(
                        "ALTER ROLE {user} SET search_path to {user}, public"
                    ).format(user=user)
                )
                # Grant schema to new user
                c.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {user}, public TO {user}").format(
                        user=user
                    )
                )
                # Equip new user with all grants
                c.execute(
                    sql.SQL("GRANT ALL ON SCHEMA {user} TO {user}").format(user=user)
                )
                # deploy the tables and indices and so on
                c.execute(query)

                c.execute(
                    sql.SQL(
                        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {user} TO {user}"
                    ).format(user=user)
                )

                c.execute(
                    sql.SQL(
                        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {user} TO {user}"
                    ).format(user=user)
                )

    def deploy_dml(self, thing):
        file = os.path.join(os.path.dirname(__file__), "sql", "postgres-dml.sql")
        with open(file) as fh:
            query = fh.read()
        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                c.execute(sql.SQL("SET search_path TO {0}").format(user))
                c.execute(query)

    def grant_sta_select(self, thing, user_prefix: str, schema: str | None = None):
        schema = sql.Identifier(schema or thing.database.username.lower())
        sta_user = sql.Identifier(
            user_prefix.lower() + thing.database.ro_username.lower()
        )
        with self.db.connection() as conn:
            with conn.cursor() as c:
                # Set default schema when connecting as user
                c.execute(
                    sql.SQL(
                        "ALTER ROLE {sta_user} SET search_path to {schema}, public"
                    ).format(sta_user=sta_user, schema=schema)
                )

                # grant read rights to newly created views in schema to user
                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON ALL TABLES in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON ALL SEQUENCES in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT EXECUTE ON ALL FUNCTIONS in SCHEMA {schema} TO {sta_user}"
                    ).format(sta_user=sta_user, schema=schema)
                )

    def grant_grafana_select(self, thing, user_prefix: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                schema = sql.Identifier(thing.database.username.lower())
                grf_user = sql.Identifier(
                    user_prefix.lower() + thing.database.ro_username.lower()
                )

                # Set default schema when connecting as user
                c.execute(
                    sql.SQL("ALTER ROLE {grf_user} SET search_path to {schema}").format(
                        grf_user=grf_user, schema=schema
                    )
                )

                c.execute(sql.SQL("SET search_path TO {schema}").format(schema=schema))

                c.execute(
                    sql.SQL(
                        "REVOKE ALL ON ALL TABLES IN SCHEMA {schema}, public FROM {grf_user}"
                    ).format(grf_user=grf_user, schema=schema)
                )

                c.execute(
                    sql.SQL(
                        "GRANT SELECT ON TABLE thing, datastream, observation, "
                        'journal, datastream_properties, "LOCATIONS", "THINGS", '
                        '"THINGS_LOCATIONS", "SENSORS", "OBS_PROPERTIES", "DATASTREAMS", '
                        '"OBSERVATIONS" TO {grf_user}'
                    ).format(grf_user=grf_user, schema=schema)
                )

    def create_frost_views(self, thing, internal: bool = False):
        base_path = os.path.join(os.path.dirname(__file__), "sql", "sta_views")
        files = [
            os.path.join(base_path, "schema_context.sql"),
            os.path.join(base_path, "thing.sql"),
            os.path.join(base_path, "location.sql"),
            os.path.join(base_path, "sensor.sql"),
            os.path.join(base_path, "observed_property.sql"),
            os.path.join(base_path, "datastream.sql"),
            os.path.join(base_path, "helper_views", "foi_ts_action_type_coord.sql"),
            os.path.join(base_path, "helper_views", "obs_ts_action_type_coord.sql"),
            os.path.join(base_path, "feature.sql"),
            os.path.join(base_path, "observation.sql"),
        ]

        schema = thing.database.schema.lower()
        # Schema the views are actually deployed into (used by feature.sql to
        # find/drop a pre-existing FEATURES in the *target* schema). This differs
        # from {tsm_schema}, which stays the project schema as it is the
        # datasource_id the views filter on.
        target_schema = schema + INTERNAL_SUFFIX if internal else schema
        user = sql.Identifier(thing.database.username.lower())
        SMS_URL = os.environ.get("SMS_URL")
        CV_URL = os.environ.get("CV_URL")

        def escape_quote(s: str) -> str:
            return s.replace("'", "''")

        with self.db.connection() as conn:
            with conn.cursor() as c:
                if internal:
                    # Deploy identical views into the "_internal" schema. Keep the
                    # project schema OUT of the search_path: otherwise the files'
                    # `DROP VIEW IF EXISTS "OBSERVATIONS"` would, on the first run
                    # (empty internal schema), fall through and drop the *public*
                    # view in the project schema. Sibling helper views resolve to
                    # the internal schema; the sole raw table (observation) is
                    # qualified explicitly below.
                    c.execute(
                        sql.SQL("SET search_path TO {internal}, public").format(
                            internal=sql.Identifier(
                                thing.database.username.lower() + INTERNAL_SUFFIX
                            ),
                        )
                    )
                else:
                    c.execute(sql.SQL("SET search_path TO {user}").format(user=user))
                for file in files:
                    logger.debug(f"deploy file: {file}")
                    with open(file) as fh:
                        view = fh.read()
                    # This is a possible entry point for SQL injections. Ensure that we have
                    # full control over the values, especially that the value does not come
                    # from userinput. Additionally, we escape single quotes, prevent closing
                    # the outer quotes in the file.
                    view = view.replace("{tsm_schema}", f"{escape_quote(schema)}")
                    view = view.replace(
                        "{target_schema}", f"{escape_quote(target_schema)}"
                    )
                    view = view.replace("{sms_url}", f"{escape_quote(SMS_URL)}")
                    view = view.replace("{cv_url}", f"{escape_quote(CV_URL)}")
                    if internal:
                        # Relax the visibility filter to public OR internal. is_public
                        # only ever appears qualified as c.<> (sms_configuration) and
                        # d.<> (sms_device), so these two replacements are exhaustive.
                        view = view.replace(
                            "c.is_public", "(c.is_public OR c.is_internal)"
                        )
                        view = view.replace(
                            "d.is_public", "(d.is_public OR d.is_internal)"
                        )
                        # `observation` is the only raw project table referenced
                        # unqualified; qualify it since the project schema is not on
                        # the search_path for the internal deploy (see above).
                        view = re.sub(
                            r"\bobservation\b", f'"{schema}".observation', view
                        )
                    c.execute(view)

    def create_grafana_views(self, thing):
        file = os.path.join(
            os.path.dirname(__file__),
            "sql",
            "grafana_views",
            "datastream_properties.sql",
        )
        with open(file) as fh:
            view = fh.read()
        with self.db.connection() as conn:
            with conn.cursor() as c:
                user = sql.Identifier(thing.database.username.lower())
                c.execute(sql.SQL("SET search_path TO {0}").format(user))
                c.execute(view)

    def upsert_thing(self, thing) -> bool:
        """Returns True for insert and False for update"""
        schema_name = thing.database.username.lower()
        query = (
            f"INSERT INTO {schema_name}.thing (name, uuid, description, properties) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (uuid) DO UPDATE SET "
            "name = EXCLUDED.name, "
            "description = EXCLUDED.description, "
            "properties = EXCLUDED.properties "
            "RETURNING (xmax = 0)"
        )
        params = (
            thing.name,
            thing.uuid,
            thing.description,
            json.dumps(thing.properties),
        )
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(query, params)
                result = c.fetchone()
        return result

    def thing_exists(self, username: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [username])
                return len(c.fetchall()) > 0

    def user_exists(self, username: str):
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", [username])
                return len(c.fetchall()) > 0

    def upsert_schema_thing_mapping(self, thing):
        # This ensures that we don't compare
        # None to None later at the early exit.
        if thing.database.username is None:
            raise ValueError("schema must not be None")

        q = "SELECT schema FROM public.schema_thing_mapping WHERE thing_uuid=%s"
        with self.db.connection() as conn:
            with conn.cursor() as c:
                curr_schema = c.execute(cast(Literal, q), [thing.uuid]).fetchone()

        if curr_schema is not None:
            curr_schema = curr_schema[0]

        if curr_schema == thing.database.username:
            logger.debug(f"thing:schema mapping already exists")
            return

        q = (
            "INSERT INTO public.schema_thing_mapping (schema, thing_uuid) "
            "VALUES (%s::varchar(100), %s::uuid) "
            "ON CONFLICT (schema, thing_uuid) DO UPDATE SET "
            "schema = EXCLUDED.schema, "
            "thing_uuid = EXCLUDED.thing_uuid "
        )
        with self.db.connection() as conn:
            with conn.cursor() as c:
                c.execute(cast(Literal, q), [thing.database.username, thing.uuid])
        if curr_schema is None:
            logger.info(f"created thing:schema mapping in DB for thing {thing.uuid}")
        else:
            logger.info(f"updated thing:schema mapping in DB for thing {thing.uuid}")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInPostgresHandler().run_loop()
