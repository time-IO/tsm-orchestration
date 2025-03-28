#! /usr/bin/env python3

# UBA API docs: https://www.umweltbundesamt.de/daten/luft/luftdaten/doc

import requests
import os
import logging
import json
import click

from datetime import datetime, timedelta
import timeio.mqtt as mqtt

from timeio.journaling import Journal

journal = Journal("CronJob")
api_base_url = os.environ.get("DB_API_BASE_URL")


def adjust_datetime(datetime_str: str) -> str:
    """UBA API returns datetime format with hours from 1 to 24 so it
    has to be parsed for timeIO DB API
    """
    date = datetime.strptime(datetime_str[0:10], "%Y-%m-%d")
    date_adjusted = date + timedelta(days=1)

    return date_adjusted.strftime("%Y-%m-%d %H:%M:%S")


def get_timerange_parameters():
    """UBA API expects time_from/time_to in the range of 1 to 24"""
    datetime_now = datetime.now()
    datetime_from = datetime_now - timedelta(hours=1)
    if datetime_now.hour == 0:
        time_to = 24
        date_to = (datetime_now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        time_to = datetime_now.hour
        date_to = datetime_now.strftime("%Y-%m-%d")

    if datetime_from.hour == 0:
        time_from = 24
        date_from = (datetime_from - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        time_from = datetime_from.hour
        date_from = datetime_from.strftime("%Y-%m-%d")

    return date_from, time_from, date_to, time_to


def get_components_and_scopes():
    """Get components (i.e measured quantites) and scopes
    (aggregation infos) for later mapping
    """
    response_components = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/components/json"
    )
    response_components.raise_for_status()
    response_scopes = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/scopes/json"
    )
    response_scopes.raise_for_status()
    components = {
        int(v[0]): v[1]
        for k, v in response_components.json().items()
        if k not in ["count", "indices"]
    }
    scopes = {
        int(v[0]): v[1]
        for k, v in response_scopes.json().items()
        if k not in ["count", "indices"]
    }
    return components, scopes


def get_station_info(station_id: str) -> list:
    """Get all available components and scope combinations of a given
    station
    """
    station_info = list()
    response = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/measures/limits"
    )
    response.raise_for_status()
    response_json = response.json()["data"]
    for k, v in response_json.items():
        if v[2] == station_id:
            station_info.append({"scope": int(v[0]), "component": int(v[1])})
    return station_info


def request_measure_endpoint(
    station_id: str,
    component_id: int,
    scope_id: int,
    date_from: str,
    date_to: str,
    time_from: int,
    time_to: int,
) -> dict:
    """Request uba api measure endpoint for a given component and scope
    and a given time range
    """
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "time_from": time_from,
        "time_to": time_to,
        "station": station_id,
        "component": component_id,
        "scope": scope_id,
    }
    response = requests.get(
        url="https://www.umweltbundesamt.de/api/air_data/v3/measures/json",
        params=params,
    )
    response.raise_for_status()
    response_json = response.json()
    if response_json["data"]:
        return response_json["data"][station_id]
    else:
        return response_json["data"]


def combine_measure_responses(
    station_id: str,
    date_from: str,
    date_to: str,
    time_from: int,
    time_to: int,
    components: dict,
    scopes: dict,
) -> list:
    """Combine uba respones for all component/scope combinations into
    one object
    """
    measure_data = list()
    station_info = get_station_info(station_id)
    for entry in station_info:
        response = request_measure_endpoint(
            station_id,
            entry["component"],
            entry["scope"],
            date_from,
            date_to,
            time_from,
            time_to,
        )
        for k, v in response.items():
            measure_data.append(
                {
                    "timestamp": v[3],
                    "value": v[2],
                    "measure": f"{components[entry['component']]} {scopes[entry['scope']]}",
                }
            )
    return measure_data


def parse_measure_data(measure_data: list, station_id: str) -> list:
    """Creates POST body from combined uba measures data"""
    bodies = []
    source = {
        "uba_station_id": station_id,
        "endpoint": "/measures",
    }
    for entry in measure_data:
        if entry["timestamp"][11:13] == "24":
            entry["timestamp"] = adjust_datetime(entry["timestamp"])
        if entry["value"]:
            body = {
                "result_time": entry["timestamp"],
                "result_type": 0,
                "result_number": entry["value"],
                "datastream_pos": entry["measure"],
                "parameters": json.dumps(
                    {"origin": "uba_data", "column_header": source}
                ),
            }
            bodies.append(body)
    return bodies


def get_airquality_data(
    station_id: str,
    date_from: str,
    date_to: str,
    time_from: int,
    time_to: int,
    components: dict,
) -> list:
    """Request uba api airquality endpoint for a given station_id and
    time range
    """
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "time_from": time_from,
        "time_to": time_to,
        "station": station_id,
    }
    response = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/airquality/json", params=params
    )
    response.raise_for_status()
    response_json = response.json()
    if not response_json["data"]:
        return []

    response_data = response_json["data"][station_id]
    aqi_data = []
    for k, v in response_data.items():
        pollutant_info = list()
        for i in range(3, len(v)):
            entry = {"component": components[v[i][0]], "airquality_index": v[i][2]}
            pollutant_info.append(entry)
        aqi_data.append(
            {
                "timestamp": v[0],
                "airquality_index": v[1],
                "data_complete": v[2],
                "pollutant_info": pollutant_info,
            }
        )
    return aqi_data


def parse_aqi_data(aqi_data: list, station_id: str) -> list:
    """Creates POST body from uba air quality data"""
    bodies = []
    for entry in aqi_data:
        source = {
            "uba_station_id": station_id,
            "endpoint": "/airquality",
            "pollutant_info": entry["pollutant_info"],
        }
        if entry["timestamp"][11:13] == "24":
            entry["timestamp"] = adjust_datetime(entry["timestamp"])
        if entry["airquality_index"]:
            body = {
                "result_time": entry["timestamp"],
                "result_type": 0,
                "result_number": entry["airquality_index"],
                "datastream_pos": "AQI",
                "parameters": json.dumps(
                    {"origin": "uba_data", "column_header": source}
                ),
            }
            bodies.append(body)
    return bodies


@click.command()
@click.argument("thing_uuid")
@click.argument("parameters")
@click.argument("target_uri")
def main(thing_uuid, parameters, target_uri):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
    logger = logging.getLogger("extApi_sync.uba")

    logger.info(f"Start fetching UBA data for thing {thing_uuid}")
    params = json.loads(parameters.replace("'", '"'))
    date_from, time_from, date_to, time_to = get_timerange_parameters()
    components, scopes = get_components_and_scopes()
    measure_data = combine_measure_responses(
        params["station_id"], date_from, date_to, time_from, time_to, components, scopes
    )
    aqi_data = get_airquality_data(
        params["station_id"], date_from, date_to, time_from, time_to, components
    )
    parsed_measure_data = parse_measure_data(measure_data, params["station_id"])
    parsed_aqi_data = parse_aqi_data(aqi_data, params["station_id"])
    parsed_observations = {"observations": parsed_measure_data + parsed_aqi_data}
    logger.info(f"Finished fetching UBA data for thing {thing_uuid}")
    resp = requests.post(
        f"{api_base_url}/observations/upsert/{thing_uuid}",
        json=parsed_observations,
        headers={"Content-type": "application/json"},
    )
    if resp.status_code != 200:
        journal.error(
            f"Failed to insert UBA data into timeIO DB: {resp.text}", thing_uuid
        )
        resp.raise_for_status()
        # exit

    journal.info(
        f"Successfully inserted {len(parsed_observations['observations'])} "
        f"observations for thing {thing_uuid} from UBA API into timeIO DB",
        thing_uuid,
    )
    mqtt.publish_single("data_parsed", json.dumps({"thing_uuid": thing_uuid}))


if __name__ == "__main__":
    main()
