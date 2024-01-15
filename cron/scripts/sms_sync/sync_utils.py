import psycopg2
from psycopg2 import sql as psysql
from typing import Dict, AnyStr, Optional
from psycopg2.extensions import cursor, connection
from urllib.request import urlopen, Request
from urllib.parse import urljoin
import json
from datetime import datetime
from os import environ
import time
from functools import reduce
from operator import getitem


def get_utc_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)")


def get_connection_from_env(retries: int = 4, sleep: int = 3) -> connection:
    user = environ.get("CREATEDB_POSTGRES_USER")
    password = environ.get("CREATEDB_POSTGRES_PASSWORD")
    host = environ.get("CREATEDB_POSTGRES_HOST")
    db = environ.get("CREATEDB_POSTGRES_DATABASE")
    for _ in range(retries):
        try:
            return psycopg2.connect(
                database=db, user=user, password=password, host=host
            )
        except Exception as e:
            print(f"{get_utc_str()}: Retrying...")
            time.sleep(sleep)
    print(f"{get_utc_str()}: Exiting...")
    exit(1)


def get_data_from_url(url: str, endpoint: str, token: Optional[str] = None) -> Dict:
    target = urljoin(url, endpoint)
    print(f"{get_utc_str()}: Getting data from {target}")
    all_data = []
    headers = {}
    if token:
        headers["X-APIKEY"] = token
    while True:
        request = Request(target, headers=headers)
        response = urlopen(request)
        data = json.loads(response.read())
        all_data.extend(data["data"])
        try:
            target = data["links"]["next"]
        except KeyError:
            break
        if target is None:
            break
    data["data"] = all_data
    return data


def _get_value_from_dict(data: dict, path: list) -> AnyStr:
    val = reduce(getitem, path, data)
    try:
        return f"{int(val)}"
    except:
        if type(val) == str:
            # replace single quotes with double single quotes
            # to make it work with postgres
            val = val.replace("'", "''")
        # return string in single quotes
        # also to make it work with postgres
        return f"'{val}'"


def _table_is_foreign(c: cursor, table_name: str) -> bool:
    query = psysql.SQL(
        """
        SELECT table_type FROM information_schema.tables 
        WHERE table_name=%s
        """
    )
    c.execute(query, (table_name,))
    r = c.fetchone()
    if r is None:
        return False
    else:
        return r[0] == "FOREIGN"


def _drop_foreign_table(c: cursor, table_name: str) -> None:
    query = psysql.SQL("DROP FOREIGN TABLE IF EXISTS {table_identifier};").format(
        table_identifier=psysql.Identifier(table_name)
    )
    if _table_is_foreign(c=c, table_name=table_name):
        try:
            c.execute(query, (table_name,))
            # return c.fetchall()
        except Exception as e:
            print(f"Can not drop foreign table {table_name}:\n{e}")


def _table_create_query(table_dict: dict) -> str:
    columns = table_dict["keys"]
    query = f"CREATE TABLE IF NOT EXISTS {table_dict['name']} ("
    for key, value in columns.items():
        query += f"{key} {value['type']}, "
    return query.rstrip(", ") + ");"


def _table_insert_query(table_dict: dict, data: dict) -> str:
    columns = table_dict["keys"]
    query = f"INSERT INTO {table_dict['name']} ("
    for key, value in columns.items():
        query += f"{key},"
    query = query.rstrip(",") + ") VALUES ("
    for key, value in columns.items():
        query += f"'{reduce(getitem, value['path'], data)}',"
    return query.rstrip(",") + ");"


def create_table_if_not_exists(c: cursor, table_dict: Dict) -> None:
    _drop_foreign_table(c=c, table_name=table_dict["name"])
    create_query = _table_create_query(table_dict)
    c.execute(create_query)


def update_table(c: cursor, url: str, table_dict: dict, token: Optional[str] = None) -> None:
    if token:
        data = get_data_from_url(url=url, endpoint=table_dict["endpoint"], token=token)
    else:
        data = get_data_from_url(url=url, endpoint=table_dict["endpoint"])
    query = f"INSERT INTO {table_dict['name']} ("
    for key in table_dict["keys"]:
        query += f"{key}, "
    query = query.rstrip(", ") + ") VALUES "
    for item in data["data"]:
        values = "("
        for key, value in table_dict["keys"].items():
            value = _get_value_from_dict(item, value["path"])
            if value == "None":
                value = "NULL"
            values += value + ", "
        values = values.rstrip(", ") + "), "
        query += values
    query = query.rstrip(", ")
    query += " ON CONFLICT (id) DO UPDATE SET "
    for key in table_dict["keys"]:
        if key == "id":
            continue
        query += f"{key} = EXCLUDED.{key}, "
    query = query.rstrip(", ")
    c.execute(query)
