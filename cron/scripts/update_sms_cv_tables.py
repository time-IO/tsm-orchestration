import psycopg2
from typing import Dict
from psycopg2.extensions import cursor, connection
from urllib.request import urlopen
from urllib.parse import urljoin
import json
from os import environ
import time
from datetime import datetime

def get_utc_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)")

def get_connection_from_env(retries: int=4, sleep: int=3) -> connection:
    user = environ.get("CREATEDB_POSTGRES_USER")
    password = environ.get("CREATEDB_POSTGRES_PASSWORD")
    host = environ.get("CREATEDB_POSTGRES_HOST")
    db = environ.get("CREATEDB_POSTGRES_DATABASE")
    print(f"{get_utc_str()}: Connecting on host '{host}' to db '{db}' as user '{user}' with password '{password}'")
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

def get_json_from_url(url: str, endpoint: str) -> Dict:
    target = urljoin(url, endpoint)
    print(f"{get_utc_str()}: Getting data from {target}")
    response = urlopen(target)
    data = json.loads(response.read())
    return data

def update_sms_cv_tables(url: str) -> None:
    with get_connection_from_env() as db:
        with db.cursor() as c:
            update_measured_quantity(cursor=c, url=url, endpoint="measuredquantities")
            # add more tables here

            db.commit()
            print(f"{get_utc_str()}: All tables updated")


def update_measured_quantity(cursor: cursor, url: str, endpoint: str) -> None:
    print(f"{get_utc_str()}: Updating sms_cv_measured_quantity ...")
    # create table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sms_cv_measured_quantity (
            id integer PRIMARY KEY,
            term VARCHAR(255) not null,
            provenance_uri VARCHAR(255),
            definition text
        )
        """
    )
    data = get_json_from_url(url, endpoint)
    # insert/update data
    for item in data["data"]:
        cursor.execute("""
            INSERT INTO sms_cv_measured_quantity
            (id, term, provenance_uri, definition)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
            term = EXCLUDED.term,
            provenance_uri = EXCLUDED.provenance_uri,
            definition = EXCLUDED.definition
            """,
            (
                item["id"],
                item["attributes"]["term"],
                item["attributes"]["provenance_uri"],
                item["attributes"]["definition"],
            ),
        )
    print(f"{get_utc_str()}: Updated sms_cv_measured_quantity!")


api_access = environ.get("CV_API_ACCESS")
url = environ.get("CV_API_URL")

if __name__ == "__main__" and api_access == "true":
    update_sms_cv_tables(url)
