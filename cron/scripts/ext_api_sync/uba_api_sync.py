#! /usr/bin/env python3

import requests
import os
import logging
import json
import click


api_base_url = os.environ.get("DB_API_BASE_URL")


def get_components_and_scopes():
    """Get components (i.e measured quantites) and scopes (aggregation infos) for later mapping"""
    response_components = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/components/json"
    )
    response_scopes = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/scopes/json"
    )
    if response_components.status_code == 200 and response_scopes.status_code == 200:
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
    """Get all available components and scope combinations of a given station"""
    station_info = list()
    response = requests.get(
        "https://www.umweltbundesamt.de/api/air_data/v3/measures/limits"
    )
    if response.status_code == 200:
        response_json = response.json()["data"]
        for k, v in response_json.items():
            if v[2] == station_id:
                station_info.append({"scope": int(v[0]), "component": int(v[1])})
        return station_info


def request_uba_api(
    station_id: str,
    component_id: int,
    scope_id: int,
    date_from: str,
    date_to: str,
    time_from: int,
    time_to: int,
) -> dict:
    """Request uba api measure endpoint for a given component and scope and a given time range"""
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
    if response.status_code == 200:
        response_json = response.json()["data"][station_id]
        if response_json:
            return response_json


def combine_uba_responses(
    station_id: str,
    date_from: str,
    date_to: str,
    time_from: int,
    time_to: int,
) -> list:
    """Combine uba respones for all component/scope combinations into one object"""
    uba_data = list()
    station_info = get_station_info(station_id)
    components, scopes = get_components_and_scopes()
    for entry in station_info:
        response = request_uba_api(
            station_id,
            entry["component"],
            entry["scope"],
            date_from,
            date_to,
            time_from,
            time_to,
        )
        for k, v in response.items():
            uba_data.append(
                {
                    "timestamp": v[3],
                    "value": v[2],
                    "parameter": f"{components[entry['component']]} {scopes[entry['scope']]}",
                }
            )
    return uba_data


def parse_uba_data(uba_data: list, station_id: str) -> dict:
    """Creates POST body from combined uba data"""
    bodies = []
    source = {"uba_station_id": station_id}
    for entry in uba_data:
        if entry["timestamp"][11:13] == "24":
            entry["timestamp"] = (
                entry["timestamp"][:11] + "00" + entry["timestamp"][13:]
            )
        if entry["value"]:
            body = {
                "result_time": entry["timestamp"],
                "result_type": 0,
                "result_number": entry["value"],
                "datastream_pos": entry["parameter"],
                "parameters": json.dumps(
                    {"origin": "uba_data", "column_header": source}
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
    uba_data = combine_uba_responses(params["station_id"])
    parsed_observations = parse_uba_data(uba_data, params["station_id"])
    req = requests.post(
        f"{api_base_url}/observations/upsert/{thing_uuid}",
        json=parsed_observations,
        headers={"Content-type": "application/json"},
    )
    if req.status_code == 201:
        logging.info(
            f"Successfully inserted {len(parsed_observations['observations'])} "
            f"observations for thing {thing_uuid} from UBA API into TimeIO DB"
        )
    else:
        logging.error(f"{req.text}")


if __name__ == "__main__":
    main()
