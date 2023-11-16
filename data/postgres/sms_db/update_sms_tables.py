import psycopg2
from psycopg2.extensions import cursor
from urllib.request import urlopen
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

def update_sms_cv_tables():
    cv_url = environ.get("SMS_URL")
    db = establish_connection()
    with db:
        with db.cursor() as c:            
            db.commit()

            # update_table_xyz(c)

            print("All tables updated")


# define the individual tables as separate functions here

# def update_table_xyz(cursor: cursor):
#     see update_sms_cv_tables.py

# getting the data from sms will need machine-token access, 
# that is afaik not yet available

if __name__ == "__main__":
    update_sms_cv_tables()
