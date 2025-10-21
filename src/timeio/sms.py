import os
import psycopg
import logging
import json
import time

from psycopg import sql as psysql, Connection, Cursor
from typing import Union, Dict, Optional, Any
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from datetime import datetime, timezone
from functools import reduce
from operator import getitem

from timeio.databases import Database


class SmsCVSyncer:
    def __init__(self, cv_api_url, db_conn_str):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_names = [
            "sms_cv_measured_quantity.json",
            "sms_cv_license.json",
            "sms_cv_aggregation_type.json",
            "sms_cv_unit.json",
        ]
        self.cv_api_url = cv_api_url
        self.db_conn_str = db_conn_str
        self.db = self.connect()
        self.logger = logging.getLogger("sync_sms_cv")

    def sync(self):
        file_path_list = [
            os.path.join(self.script_dir, "..", "cv_tables", file_name)
            for file_name in self.file_names
        ]

        with self.db as conn:
            with conn.cursor() as c:
                for file_path in file_path_list:
                    with open(file_path, "r") as f:
                        table_dict = json.load(f)
                    self.create_table(c=c, table_dict=table_dict)
                    self.upsert_table(c=c, url=self.cv_api_url, table_dict=table_dict)

    @staticmethod
    def get_utc_str() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S (UTC)")

    def connect(self, retries: int = 4, sleep: int = 3) -> Connection:
        err = None
        for _ in range(retries):
            try:
                return psycopg.connect(self.db_conn_str)
            except Exception as e:
                err = e
                self.logger.debug(f"{self.get_utc_str()}: Retrying...")
                time.sleep(sleep)
        raise ConnectionError(f"Could not connect to database") from err

    def get_data_from_url(
        self, url: str, endpoint: str, token: Optional[str] = None
    ) -> Dict:
        target = urljoin(url, endpoint)
        print(f"{self.get_utc_str()}: Getting data from {target}")
        all_data = []
        headers = {}
        if token:
            headers["X-APIKEY"] = token
        while True:
            request = Request(target, headers=headers)
            response = urlopen(request)
            data = json.loads(response.read())
            all_data.extend(data["data"])
            target = data.get("links", {}).get("next", None)
            if target is None:
                break
        data["data"] = all_data
        return data

    @staticmethod
    def _remove_id_duplicates(data: list) -> list:
        seen = set()
        uniq = []
        for item in data:
            if item["id"] not in seen:
                uniq.append(item)
                seen.add(item["id"])
        return uniq

    @staticmethod
    def _value_from_dict(dict_: dict, path: list) -> Union[str, int, float, bool, None]:
        return reduce(getitem, path, dict_)

    @staticmethod
    def _to_postgres_str(val: Union[str, int, float, bool, None]) -> str:
        if val is None:
            return "NULL"  # in postgres None is NULL
        if type(val) == bool:
            return f"{val}"
        if type(val) == int:
            return f"{val}"
        if type(val) == float:
            return f"{val}"
        if type(val) == str:
            try:
                # try to convert string to int
                # some integer keys are provided as string by the api
                # and need to be converted to int for postgres
                return f"{int(val)}"
            except:
                # replace single quotes with double single quotes
                # to escape single quote string termination in postgres
                val = val.replace("'", "''")
                # return string in single quotes
                # to mark it as a string for postgres
                return f"'{val}'"

    @staticmethod
    def _table_is_foreign(c: Cursor, table_name: str) -> bool:
        query = psysql.SQL(
            "SELECT table_type FROM information_schema.tables WHERE table_name=%s"
        )
        c.execute(query, (table_name,))
        r = c.fetchone()
        if r is None:
            return False
        else:
            return r[0] == "FOREIGN"

    def _drop_foreign_table(self, c: Cursor, table_name: str) -> None:
        query = psysql.SQL("DROP FOREIGN TABLE IF EXISTS {table}").format(
            table=psysql.Identifier(table_name)
        )
        if self._table_is_foreign(c=c, table_name=table_name):
            try:
                c.execute(query)
            except Exception as e:
                self.logger.error(f"Could not drop foreign table {table_name}:\n{e}")

    @staticmethod
    def _table_create_query(table_dict: dict) -> str:
        columns = table_dict["keys"]
        query = f"CREATE TABLE IF NOT EXISTS {table_dict['name']} ("
        for key, value in columns.items():
            query += f"{key} {value['type']}, "
        return query.rstrip(", ") + ");"

    def create_table(self, c: Cursor, table_dict: Dict) -> None:
        """
        creates table based on table_dict (loaded from foo-table.json in ./tables)

        e.g.:
        CREATE TABLE IF NOT EXISTS foo-table (
            id integer primary key,
            column_b varchar(255),
            column_c text,
            ...
        )
        """
        self._drop_foreign_table(c=c, table_name=table_dict["name"])
        create_query = self._table_create_query(table_dict)
        c.execute(create_query)

    def _table_upsert_query(self, table_dict: dict, data: dict) -> str:
        # TODO simplyfy with ", ".join(Iterable)
        query = f"INSERT INTO {table_dict['name']} ("
        for key in table_dict["keys"]:
            query += f"{key}, "
        query = query.rstrip(", ") + ") VALUES "
        for item in data:
            values = "("
            for key, val in table_dict["keys"].items():
                value = self._value_from_dict(item, val["path"])
                val_str = self._to_postgres_str(value)
                values += val_str + ", "
            values = values.rstrip(", ") + "), "
            query += values
        query = query.rstrip(", ")
        query += " ON CONFLICT (id) DO UPDATE SET "
        for key in table_dict["keys"]:
            if key == "id":
                continue
            query += f"{key} = EXCLUDED.{key}, "
        query = query.rstrip(", ")
        return query

    def upsert_table(
        self, c: Cursor, url: str, table_dict: dict, token: Optional[str] = None
    ) -> None:
        """
        updates table based on table_dict (loaded from foo-table.json in ./tables)
        with data queried from target

        query is built by _table_upsert_query()

        e.g.:
        INSERT INTO TABLE foo-table
            (id, column_b, column_c, ...)
        VALUES
            (1, 'foo', 'bar', ...),
            (2, 'foot', 'bard', ...),
            ...
        ON CONFLICT (id) DO UPDATE SET
            column_b = EXCLUDED.column_b,
            column_c = EXCLUDED.column_c,
            ...
        """
        name = table_dict["name"]
        endpoint = table_dict["endpoint"]
        r = self.get_data_from_url(url=url, endpoint=endpoint, token=token)
        data = self._remove_id_duplicates(r["data"])
        query = self._table_upsert_query(table_dict, data)

        try:
            c.execute(query)
            self.logger.info(f"Data successfully synced to table {name}")
        except psycopg.Error as e:
            self.logger.error(f"Could not sync data to table {name}:\n{e}")
            raise e


class SmsMaterializedViewsSyncer:
    def __init__(self, db_conn_str):
        self.db = Database(db_conn_str)
        self.materialized_views = []
        self.logger = logging.getLogger("sync_sms_views")

    def collect_materialized_views(self):
        # Get a list of materialized views with the prefix "sms_"
        query = (
            "SELECT matviewname FROM pg_matviews WHERE "
            "schemaname = 'public' AND matviewname LIKE 'sms_%' "
        )
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    self.materialized_views = cur.fetchall()
                    return self

        except psycopg.Error as e:
            self.logger.error(
                f"Error occurred during fetching materialized views: {e!r}"
            )

    def update_materialized_views(self) -> None:
        template = psysql.SQL("REFRESH MATERIALIZED VIEW CONCURRENTLY {}")
        try:
            with self.db.connection() as conn:
                with conn.cursor() as cur:
                    for matview in self.materialized_views:
                        view_name = matview[0]
                        cur.execute(template.format(psysql.Identifier(view_name)))
                        self.logger.info(f"Refreshed materialized view: {view_name}")
        except psycopg.Error as e:
            self.logger.error(
                f"Error occurred during refreshing materialized view: {e!r}"
            )
