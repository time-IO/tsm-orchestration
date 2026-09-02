#!/usr/bin/env python3

import os
import subprocess
import sys
import requests
import psycopg
from cryptography.fernet import Fernet

host = "docker"

ingest_uuid = os.environ["INGEST_UUID"]
group_uuid = os.environ["GROUP_UUID"]
db_admin_user = "postgres"
db_admin_password = "postgres"

fernet_secret = os.environ.get("FERNET_ENCRYPTION_SECRET",  "CKoB---DEFAULT-DUMMY-SECRET---0exKVH0QDLy1B=")

def log(message):
    print(message, file=sys.stderr)

#Grafana
def check_grafana_dashboard():
    auth = ("grafana", "grafana")

    url = f"http://{host}/visualization/api/dashboards/uid/{ingest_uuid}"
    response = requests.get(url, auth=auth)
    if response.status_code != 200:
        log(f"Grafana dashboard check failed: {response.status_code}")
        sys.exit(1)

    #folders
    url = f"http://{host}/visualization/api/folders/{group_uuid}"
    response = requests.get(url, auth=auth)
    if response.status_code != 200:
        log(f"Grafana folder check failed: {response.status_code}")
        sys.exit(1)

    #datasource
    url = f"http://{host}/visualization/api/datasources/uid/{group_uuid}"
    response = requests.get(url, auth=auth)
    if response.status_code != 200:
        log(f"Grafana datasource check failed: {response.status_code}")
        sys.exit(1)

    #teams
    url = f"http://{host}/visualization/api/teams/search"
    response = requests.get(url, params={"uid": group_uuid}, auth=auth)
    response.raise_for_status()
    if response.json()["totalCount"] < 1:
        log("Grafana team check failed: no team found")
        sys.exit(1)

    log("Grafana dashboard, folder, datasource and team: OK")

#DB-Query
def get_db_connection():
    return psycopg.connect(
        host=host,
        port=5432,
        user=db_admin_user,
        password=db_admin_password,
        dbname="postgres",
    )

def decrypt_password(encrypted_password):
    f = Fernet(fernet_secret)
    return f.decrypt(encrypted_password.encode()).decode()

def get_database_credentials(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.username, d.password
            FROM dsm_db.database d 
            JOIN dsm_db.permission_group pg ON pg.id = d.permission_group_id
                WHERE pg.uuid = %s
            """,
            (group_uuid,),
        )
        row = cur.fetchone()
        if row is None:
            log(f"No database entry found for permission group {group_uuid}")
            sys.exit(1)
        username, encrypted_password = row
        password = decrypt_password(encrypted_password)
        return username, password

def check_database():
    conn = get_db_connection()
    try:
        username, password = get_database_credentials(conn)
    finally:
        conn.close()
    try:
        user_conn = psycopg.connect(
            host=host,
            port=5432,
            user=username,
            password=password,
            dbname="postgres",
        )
        user_conn.close()
    except Exception as e:
        log(f"Database login check failed: {e}")
        sys.exit(1)
    log("Database login: OK")

    # Verify the thing was actually provisioned in the user's schema
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT 1 FROM "{username}".thing WHERE uuid = %s',
                (ingest_uuid,),
            )
            if cur.fetchone() is None:
                log(f"Thing check failed: no row found for uuid {ingest_uuid}")
                sys.exit(1)
    finally:
        conn.close()
    log("Thing exists in database: OK")

    return username

def check_frost(db_username):
    url = f"http://{host}/sta/{db_username}/"
    response = requests.head(url)
    if response.status_code != 200:
        log(f"FROST check failed: {response.status_code}")
        sys.exit(1)
    log("FROST check: OK")

def check_minio():
    bucket_username = os.environ["BUCKET_USERNAME"]
    bucket_password = os.environ["BUCKET_PASSWORD"]
    url = f"ftp://{host}:40021"
    result = subprocess.run(
        ["curl", "-u", f"{bucket_username}:{bucket_password}", url, "-I", "-s", "-o", "/dev/null", "-w", "%{http_code}", ],
        capture_output=True,text=True
    )
    if result.returncode != 0:
        log(f"MinIO check failed: {result.stderr}")
        sys.exit(1)
    log(f"MinIO check: OK (code {result.stdout})")


if __name__ == "__main__":
    check_grafana_dashboard()
    db_username = check_database()
    check_frost(db_username)
    check_minio()
    log("All checks passed")
