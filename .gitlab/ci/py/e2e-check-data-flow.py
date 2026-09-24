#!/usr/bin/env python3

import sys
import time
import json
import requests
import psycopg
import paho.mqtt.publish as publish


host = "docker"
realm = "timeio"
test_username = "testuser"
test_password = "changeMe123!"
client_id = "timeIO-client"

db_admin_user = "postgres"
db_admin_password = "postgres"

group_path = "/a:a:a:group:VO:Group1#"
test_observation_value = 42.0


def log(message):
    print(message, file=sys.stderr)


def get_user_token():
    url = f"http://{host}/keycloak/realms/{realm}/protocol/openid-connect/token"
    resp = requests.post(
        url,
        data={
            "client_id": client_id,
            "username": test_username,
            "password": test_password,
            "grant_type": "password",
            "scope": "openid",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def call_me_endpoint(token):
    url = f"http://{host}/data-source-management/api/me/"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    log("Called /me/ to trigger permission group sync")


def get_permission_group_id(token):
    url = f"http://{host}/data-source-management/api/permission-group/"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    items = resp.json()["items"]
    for group in items:
        if group["name"] == "VO:Group1":
            return group["id"]
    log("Permission group VO:Group1 not found")
    sys.exit(1)


def get_mqtt_parser_id(token):
    url = f"http://{host}/data-source-management/api/parser/mqtt/"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    items = resp.json()["items"]
    for parser in items:
        if parser["name"] == "campbell_cr6":
            return parser["id"]
    log("Parser campbell_cr6 not found")
    sys.exit(1)


def create_mqtt_ingest(token, permission_group_id, parser_id):
    url = f"http://{host}/data-source-management/api/ingest/mqtt/"
    ingest_name = f"e2e_test_dataflow-{int(time.time())}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": ingest_name,
            "permission_group_id": permission_group_id,
            "parser_id": parser_id,
        },
    )
    resp.raise_for_status()
    return resp.json()


def send_test_mqtt_message(ingest):
    message = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [None, None, None]},
        "properties": {
            "loggerID": "e2e-test-logger",
            "observationNames": ["test_value"],
            "observations": {
                time.strftime("%Y-%m-%dT%H:%M:%SZ"): [test_observation_value]
            },
        },
    }

    publish.single(
        topic=ingest["topic"],
        payload=json.dumps(message),
        hostname=host,
        port=1883,
        auth={"username": ingest["username"], "password": ingest["password"]},
    )
    log(f"Sent test MQTT message to topic {ingest['topic']}")


def get_schema_name(permission_group_id):
    conn = psycopg.connect(
        host=host,
        port=5432,
        user=db_admin_user,
        password=db_admin_password,
        dbname="postgres",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username FROM dsm_db.database WHERE permission_group_id = %s",
                (permission_group_id,),
            )
            row = cur.fetchone()
            if row is None:
                log(
                    f"No database entry found for permission group {permission_group_id}"
                )
                sys.exit(1)
            return row[0]
    finally:
        conn.close()


def check_observation_exists(schema_name):
    conn = psycopg.connect(
        host=host,
        port=5432,
        user=db_admin_user,
        password=db_admin_password,
        dbname="postgres",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT 1 FROM "{schema_name}".observation WHERE result_number = %s ORDER BY id DESC LIMIT 1',
                (test_observation_value,),
            )
            if cur.fetchone() is None:
                log("Observation check failed: no matching observation found")
                sys.exit(1)
    finally:
        conn.close()
    log("Observation found in database: OK")


if __name__ == "__main__":
    token = get_user_token()
    log("Got user token")
    call_me_endpoint(token)
    permission_group_id = get_permission_group_id(token)
    log(f"Using permission group id = {permission_group_id}")
    parser_id = get_mqtt_parser_id(token)
    log(f"Using parser id = {parser_id}")
    ingest = create_mqtt_ingest(token, permission_group_id, parser_id)
    log(f"Creating MQTT ingest uuid = {ingest['uuid']} ")

    log("Waiting for MQTT user provisioning...")
    time.sleep(5)

    send_test_mqtt_message(ingest)

    log("Waiting for message to be processed...")
    time.sleep(5)

    schema_name = get_schema_name(permission_group_id)
    check_observation_exists(schema_name)

    log("All data flow checks passed")
