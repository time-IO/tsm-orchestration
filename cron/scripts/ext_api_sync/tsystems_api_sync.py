#! /usr/bin/env python3

import requests
import click
import logging
import json
import os
import mqtt

from datetime import datetime, timedelta, timezone

api_base_url = os.environ.get("DB_API_BASE_URL")
tsystems_base_url = (
    "https://moc.caritc.de/sensorstation-management/api/measurements/average"
)


def unix_ts_to_str(ts_unix: int) -> str:
    """Convert unix timestamp to datetime string"""
    dt = datetime.fromtimestamp(ts_unix, tz=timezone.utc)
    ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    return ts_str


def get_bearer_token(username: str, password: str) -> str:
    """Get bearer token for API authentication"""
    auth_url = "https://lcmm.caritc.de/auth/realms/lcmm/protocol/openid-connect/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "client_id": "lcmm",
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    response = requests.post(auth_url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]


def get_utc_timerange():
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_from = now_utc - timedelta(minutes=60)
    timestamp_from_str = timestamp_from.strftime("%Y-%m-%dT%H:%M:%SZ")
    return timestamp_from_str, now_str


def request_tsystems_api(
    group: str, station_id: str, username: str, password: str
) -> list:
    bearer_token = get_bearer_token(username, password)
    time_from, time_to = get_utc_timerange()
    headers = {"Accept": "*/*", "Authorization": f"Bearer {bearer_token}"}
    params = {
        "aggregationTime": "HOURLY",
        "aggregationValues": "ALL_FIELDS",
        "from": time_from,
        "to": time_to,
    }
    response = requests.get(
        f"{tsystems_base_url}/{group}/{station_id}", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()


def parse_api_response(response: list) -> dict:
    bodies = []
    for entry in response:
        source = {"sensor_id": entry.pop("deviceId"), "aggregation_time": "hourly"}
        timestamp = entry.pop("timestamp")
        for parameter, value in entry.items():
            if value:
                body = {
                    "result_time": unix_ts_to_str(timestamp),
                    "result_type": 0,
                    "result_number": value,
                    "datastream_pos": parameter,
                    "parameters": json.dumps(
                        {"origin": "tsystems_data", "column_header": source}
                    ),
                }
                bodies.append(body)
    return {"observations": bodies}


@click.command()
@click.argument("thing_uuid")
@click.argument("parameters")
@click.argument("target_uri")
def main(thing_uuid, parameters, target_uri):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    params = json.loads(parameters.replace("'", '"'))
    response = request_tsystems_api(
        params["group"], params["station_id"], params["username"], params["password"]
    )
    parsed_observations = parse_api_response(response)
    resp = requests.post(
        f"{api_base_url}/observations/upsert/{thing_uuid}",
        json=parsed_observations,
        headers={"Content-type": "application/json"},
    )
    if resp.status_code != 201:
        logging.error(f"{resp.text}")
        resp.raise_for_status()
        # exit

    logging.info(
        f"Successfully inserted {len(parsed_observations['observations'])} "
        f"observations for thing {thing_uuid} from TSystems API into TimeIO DB"
    )
    mqtt.send_mqtt_info("data_parsed", json.dumps({"thing_uuid": thing_uuid}))


if __name__ == "__main__":
    main()
