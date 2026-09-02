#!/usr/bin/env python3

import sys
import time

import requests

host = "docker"
realm = "timeio"
test_username = "testuser"
test_password = "changeMe123!"
client_id = "timeIO-client"

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
        }
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

def create_csv_parser(token, permission_group_id):
    url = f"http://{host}/data-source-management/api/parser/csv/"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": f"e2e-test-parser-csv-{int(time.time())}",
            "permission_group_id": permission_group_id,
            "delimiter": ",",
            "timezone": "UTC",
            "encoding": "utf_8",
            "timestamp_columns": [
                {"column": 0, "timestamp_format": "%Y-%m-%d %H:%M:%S"}
            ],
        }
    )
    resp.raise_for_status()
    return resp.json()["id"]

def create_ingest(token, permission_group_id, parser_id):
    url = f"http://{host}/data-source-management/api/ingest/external-sftp/"
    ingest_name = f"e2e-test-ingest-{int(time.time())}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": ingest_name,
            "permission_group_id": permission_group_id,
            "parser_id": parser_id,
            "uri": "sftp.example.com",
            "path": "/data",
            "filename_pattern": "*.csv",
        }
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    token = get_user_token()
    log("Got user token")
    call_me_endpoint(token)
    permission_group_id = get_permission_group_id(token)
    log(f"Using permission group id = {permission_group_id}")
    parser_id = create_csv_parser(token, permission_group_id)
    log(f"Using parser id = {parser_id}")
    ingest = create_ingest(token, permission_group_id, parser_id)
    log(f"Creating ingest uuid = {ingest['uuid']}")

    print(f"export INGEST_UUID={ingest['uuid']}", flush=True)
    print(f"export GROUP_UUID={ingest['permission_group']['uuid']}", flush=True)
    print(f"export BUCKET_USERNAME={ingest['bucket_username']}", flush=True)
    print(f"export BUCKET_PASSWORD={ingest['bucket_password']}", flush=True)