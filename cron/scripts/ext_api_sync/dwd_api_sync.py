#! /usr/bin/env python3

import requests
import os
import logging
import json
import click

from datetime import datetime, timedelta

api_base_url = os.environ.get("DB_API_BASE_URL")

PARAMETER_MAPPING = {
    "cloud_cover": 0,
    "condition": 1,
    "dew_point": 0,
    "icon": 1,
    "precipitation": 0,
    "precipitation_probability": 0,
    "precipitation_probability_6h": 0,
    "pressure_msl": 0,
    "relative_humidity": 0,
    "solar": 0,
    "sunshine": 0,
    "temperature": 0,
    "visibility": 0,
    "wind_direction": 0,
    "wind_speed": 0,
    "wind_gust_direction": 0,
    "wind_gust_speed": 0
}

RESULT_TYPE_MAPPING = {0: "result_number",
                       1: "result_string",
                       2: "result_json",
                       3: "result_boolean"}


def fetch_brightsky_data(station_id: str, brightsky_base_url = "https://api.brightsky.dev/weather") -> dict:
    """ Returns DWD data with hourly resolution of yesterday"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_start = datetime.strftime(yesterday, '%Y-%m-%d:00:00:00')
    yesterday_end = datetime.strftime(yesterday, '%Y-%m-%d:23:55:00')
    params = {"dwd_station_id": station_id,
              "date": yesterday_start,
              "last_date": yesterday_end,
              "units": "dwd"}
    brightsky_response = requests.get(url=brightsky_base_url, params=params)
    response_data = brightsky_response.json()
    return response_data

def parse_brightsky_response(resp) -> dict:
    """ Uses Brightsky Response and returns body for POST request"""
    observation_data = resp["weather"]
    source = resp["sources"][0]
    bodies = []
    for obs in observation_data:
        timestamp = obs.pop("timestamp")
        del obs["source_id"]
        for parameter, value in obs.items():
            if value:
                result_type = PARAMETER_MAPPING[parameter]
                body = {
                    "result_time": timestamp,
                    "result_type": result_type,
                    "datastream_pos": parameter,
                    RESULT_TYPE_MAPPING[result_type]: value,
                    "parameters": json.dumps({"origin": "dwd_data", "column_header": source})
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
    response = fetch_brightsky_data(params["station_id"])
    parsed_observations = parse_brightsky_response(response)
    req = requests.post(f"{api_base_url}/observations/upsert/{thing_uuid}",
                        json=parsed_observations,
                        headers = {'Content-type': 'application/json'})
    if req.status_code == 201:
        logging.info(
            f"Successfully inserted {len(parsed_observations['observations'])} "
            f"observations for thing {thing_uuid} from DWD API into TimeIO DB"
        )
    else:
        logging.error(f"{req.text}")


if __name__ == "__main__":
    main()

