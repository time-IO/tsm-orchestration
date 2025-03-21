#!/usr/bin/python3

import os
import psycopg
from psycopg import sql as psysql
from psycopg import connection, cursor
from typing import Union, Dict, Optional, Any
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
    err = None
    for _ in range(retries):
        try:
            return psycopg.connect(dbname=db, user=user, password=password, host=host)
        except Exception as e:
            err = e
            print(f"{get_utc_str()}: Retrying...")
            time.sleep(sleep)
    raise RuntimeError(f"Could not connect to database") from err


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


def _remove_id_duplicates(data: list) -> list:
    seen = set()
    uniq = []
    for item in data:
        if item["id"] not in seen:
            uniq.append(item)
            seen.add(item["id"])
    return uniq


def _value_from_dict(dict: dict, path: list) -> Union[str, int, float, bool, None]:
    return reduce(getitem, path, dict)


def _to_postgres_str(val: Union[str, int, float, bool, None]) -> str:
    if val is None:
        # in postgres None is NULL
        return "NULL"
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


def create_table(c: cursor, table_dict: Dict) -> None:
    """
    creates table based on table_dict (loaded from foo-table.json in ./tables)

    query is built by _table_create_query()

    e.g.:
    CREATE TABLE IF NOT EXISTS foo-table (
        id integer primary key,
        column_b varchar(255),
        column_c text,
        ...
    )
    """
    _drop_foreign_table(c=c, table_name=table_dict["name"])
    create_query = _table_create_query(table_dict)
    c.execute(create_query)


def _table_upsert_query(table_dict: dict, data: dict) -> str:
    query = f"INSERT INTO {table_dict['name']} ("
    for key in table_dict["keys"]:
        query += f"{key}, "
    query = query.rstrip(", ") + ") VALUES "
    for item in data:
        values = "("
        for key, val in table_dict["keys"].items():
            value = _value_from_dict(item, val["path"])
            val_str = _to_postgres_str(value)
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
    c: cursor, url: str, table_dict: dict, token: Optional[str] = None
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
    if token:
        r = get_data_from_url(url=url, endpoint=table_dict["endpoint"], token=token)
    else:
        r = get_data_from_url(url=url, endpoint=table_dict["endpoint"])
    data = _remove_id_duplicates(r["data"])
    query = _table_upsert_query(table_dict, data)
    try:
        c.execute(query)
        print(f"Data successfully synced to table {table_dict['name']}")
    except Exception as e:
        print(f"Could not sync data to table {table_dict['name']}:\n{e}")
        raise e


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    file_names = [
        "sms_cv_measured_quantity.json",
        "sms_cv_license.json",
        "sms_cv_aggregation_type.json",
        "sms_cv_unit.json",
    ]

    file_path_list = [
        os.path.join(script_dir, "cv_tables", file_name) for file_name in file_names
    ]
    url = os.environ.get("CV_API_URL")
    home = os.environ.get("HOME")
    os.chdir(home)

    for file_path in file_path_list:
        db = get_connection_from_env()
        try:
            with db:
                with db.cursor() as c:
                    with open(file_path, "r") as f:
                        table_dict = json.load(f)
                    create_table(c=c, table_dict=table_dict)
                    upsert_table(c=db.cursor(), url=url, table_dict=table_dict)
        finally:
            db.close()
