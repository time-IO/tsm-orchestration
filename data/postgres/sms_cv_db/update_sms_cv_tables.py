import psycopg2
from urllib.request import urlopen
import json
from os import environ as env
import time


def get_connection():
    user = env.get("POSTGRES_USER")
    password = env.get("POSTGRES_PASSWORD")
    host = "localhost"
    db = "postgres"
    print(f"connecting to {db} on {host} as {user} with password {password}")
    try:
        conn = psycopg2.connect(
            database=db, user=user, password=password, host=host, port="5432"
        )
        return conn
    except Exception as e:
        print(e)
        return None

def establish_connection():
    retries = 12
    sleep = 5
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

def update_measured_quantity():
    cv_url = env.get("CV_URL")
    db = establish_connection()
    with db:
        with db.cursor() as cur:
            print("Updating sms_cv_measured_quantity table...")
            # create table if not exists
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sms_cv_measured_quantity (
                    id integer PRIMARY KEY,
                    term VARCHAR(255) not null,
                    provenance_uri VARCHAR(255),
                    definition text
                )
                """
            )

            response = urlopen(cv_url)
            data = json.loads(response.read())
            for item in data["data"]:
                cur.execute("""
                    INSERT INTO sms_cv_measured_quantity (id, term, provenance_uri, definition)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        int(item["id"]),
                        item["attributes"]["term"],
                        item["attributes"]["provenance_uri"],
                        item["attributes"]["definition"],
                    ),
                )
            db.commit()
            print("sms_cv_measured_quantity table updated")


if __name__ == "__main__":
    update_measured_quantity()
