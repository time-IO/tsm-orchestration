#! /usr/bin/env python3

import click
import base64
import json
import os
import logging
import requests

from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

api_base_url = os.environ.get("DB_API_BASE_URL")

PARAMETER_MAPPING = {
    "CO_3_CORR": 1,
    "ESP_0_RH_AVG": 1,
    "ESP_0_TEMP_AVG": 1,
    "ES_0_PRESS": 1,
    "NO2_1_CORR": 1,
    "O3_0_CORR": 1,
    "PS_0_PM10_CORR": 1,
    "PS_0_PM2P5_CORR": 1,
    "SO2_2_CORR": 1,
    "SO2_2_CORR_1hr": 1
}

RESULT_TYPE_MAPPING = {1: "result_number",
                       2: "result_string",
                       3: "result_boolean",
                       4: "result_json"}


def basic_auth(username, password):
    credential = f"{username}:{password}"
    b_encoded_credential = base64.b64encode(credential.encode('ascii')).decode('ascii')
    return f"Basic {b_encoded_credential}"

def make_request(server_url, user, password, post_data=None):
    r = Request(server_url)
    r.add_header('Authorization',  basic_auth(user, password))
    r.add_header('Content-Type', 'application/json')
    r.add_header('Accept', 'application/json')
    r_data = post_data
    r.data = r_data
    handle = urlopen(r)
    content = handle.read().decode('utf8')
    response = json.loads(content)
    return response

def get_utc_timestamps(period: int):
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_from = now_utc - timedelta(minutes=period)
    timestamp_from_str = timestamp_from.strftime("%Y-%m-%dT%H:%M:%SZ")
    return timestamp_from_str, now_str

def parse_api_response(response: list, origin: str):
    bodies = []
    for entry in response:
        obs = entry["payload"]
        source = {"sensor_id": obs.pop("deviceID"),
                  "observation_type": obs.pop("Type")}
        timestamp = obs.pop("UTC")
        for parameter, value in obs.items():
            if value:
                result_type = PARAMETER_MAPPING[parameter]
                body = {
                    "result_time": timestamp,
                    "result_type": result_type,
                    "datastream_pos": parameter,
                    RESULT_TYPE_MAPPING[result_type]: value,
                    "parameters": json.dumps({"origin": "bosch_data", "column_header": source})
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
    timestamp_from, timestamp_to = get_utc_timestamps(params["period"])
    url = f"""{params["endpoint"]}/{params["sensor_id"]}/{timestamp_from}/{timestamp_to}"""
    response = make_request(url, params["username"], params["password"])
    parsed_observations = parse_api_response(response, origin="bosch_data")
    req = requests.post(f"{api_base_url}/observations/{thing_uuid}",
                        json=parsed_observations,
                        headers = {'Content-type': 'application/json'})
    if req.status_code == 201:
        logging.info(f"""Successfully inserted {len(parsed_observations["observations"])} observations for thing {thing_uuid} from Bosch API into TimeIO DB""")
    else:
       logging.error(f"{req.text}")

if __name__ == "__main__":
    main()
