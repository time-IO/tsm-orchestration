import psycopg2
from psycopg2.extensions import cursor
from urllib.request import urlopen
from urllib.parse import urljoin
import json
from os import environ
import time
from datetime import datetime

def get_utc_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)")

def get_connection():
    user = environ.get("CREATEDB_POSTGRES_USER")
    password = environ.get("CREATEDB_POSTGRES_PASSWORD")
    host = environ.get("CREATEDB_POSTGRES_HOST")
    db = environ.get("CREATEDB_POSTGRES_DATABASE")
    print(f"{get_utc_str()}: Connecting to {db} on {host} as {user} with password {password}")
    retries = 4
    sleep = 3
    while retries > 0:
        try:
            db = psycopg2.connect(
                database=db, user=user, password=password, host=host
            )
            return db
        except Exception as e:
            print(f"{get_utc_str()}: Retrying...")
            retries -= 1
            time.sleep(sleep)
    print(f"{get_utc_str()}: Exiting...")
    exit(1)

def get_json_from_url(url: str, endpoint: str):
    print(f"{get_utc_str()}: Getting data from {urljoin(url, endpoint)}")
    response = urlopen(urljoin(url, endpoint))
    data = json.loads(response.read())
    return data

def update_sms_cv_tables(url: str):
    db = get_connection()
    with db:
        with db.cursor() as c:
            update_measured_quantity(cursor=c, url=url, endpoint="measuredquantities")
            # add more tables here

            db.commit()
            print(f"{get_utc_str()}: All tables updated")

def update_measured_quantity(cursor: cursor, url: str, endpoint: str):
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


if __name__ == "__main__":
    cv_url = environ.get("CV_API_URL")
    update_sms_cv_tables(cv_url)
