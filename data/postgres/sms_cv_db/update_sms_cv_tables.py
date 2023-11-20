import psycopg2
from psycopg2.extensions import cursor
from urllib.request import urlopen
from urllib.parse import urljoin
import json
from os import environ
import time


def get_connection():
    user = environ.get("POSTGRES_USER")
    password = environ.get("POSTGRES_PASSWORD")
    host = "localhost"
    db = "postgres"
    port="5432"
    print(f"connecting to {db} on {host} as {user} with password {password}")
    try:
        conn = psycopg2.connect(
            database=db, user=user, password=password, host=host, port=port
        )
        return conn
    except Exception as e:
        print(e)
        return None

def establish_connection():
    retries = 30
    sleep = 1
    connected = False
    while not connected and retries > 0:
        db = get_connection()
        if db:
            connected = True
        else:
            print("Retrying...")
            time.sleep(sleep)
            retries -= 1
    if not connected:
        print("Exiting...")
        exit(1)
    return db

def update_sms_cv_tables(cv_url: str):
    db = establish_connection()
    with db:
        with db.cursor() as c:
            update_measured_quantity(cursor=c, url=cv_url, endpoint="measuredquantities")
            # add more tables here

            db.commit()
            print("All tables updated")

def get_json_from_url(url: str, endpoint: str):
    response = urlopen(urljoin(url, endpoint))
    data = json.loads(response.read())
    return data

def update_measured_quantity(cursor: cursor, url: str, endpoint: str):
    print("Updating sms_cv_measured_quantity ...")
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
    print("Updated sms_cv_measured_quantity table!")


if __name__ == "__main__":
    cv_url = environ.get("CV_URL")
    update_sms_cv_tables(cv_url)
