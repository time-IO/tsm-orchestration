#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import json
from datetime import datetime

import click
import requests
import psycopg
import timeio.mqtt as mqtt


URL = "http://www.nmdb.eu/nest/draw_graph.php"
api_base_url = os.environ.get("DB_API_BASE_URL")


def get_nm_station_data(
    station: str, resolution: int, start_date: datetime, end_date: datetime
) -> dict:
    params = {
        "wget": 1,
        "stations[]": station,
        "tabchoice": "revori",
        "dtype": "corr_for_efficiency",
        "tresolution": resolution,
        "force": 1,
        "date_choice": "bydate",
        "start_year": {start_date.year},
        "start_month": {start_date.month},
        "start_day": {start_date.day},
        "start_hour": {start_date.hour},
        "start_min": {start_date.min},
        "end_year": {end_date.year},
        "end_month": {end_date.month},
        "end_day": {end_date.day},
        "end_hour": {end_date.hour},
        "end_min": {end_date.min},
        "yunits": 0,
    }
    res = requests.get(URL, params=params)
    rows = [r.split(";") for r in re.findall(r"^\d.*", res.text, flags=re.MULTILINE)]
    bodies = []
    header = {"sensor_id": station, "resolution": resolution, "nm_api_url": URL}
    for timestamp, value in rows:
        if value:
            bodies.append(
                {
                    "result_time": timestamp,
                    "result_type": 0,
                    "datastream_pos": station,
                    "result_number": float(value),
                    "parameters": json.dumps(
                        {"origin": "nm_data", "column_header": header}
                    ),
                }
            )
    return {"observations": bodies}


def get_datastream(uri: str, thing_uuid: str) -> int:
    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT datastream.id FROM datastream
                JOIN thing ON thing.id = datastream.thing_id
                WHERE thing.uuid = %s
                """,
                (thing_uuid,),
            )
            datastream_id = cur.fetchone()[0]
    return datastream_id


def get_latest_observation(uri: str, datastream_id: int) -> datetime:
    start_date = datetime(2000, 1, 1)
    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT max(result_time) FROM observation WHERE datastream_id = %s
                """,
                (datastream_id,),
            )
            date = cur.fetchone()[0]
            if date:
                start_date = date
    return start_date


@click.command()
@click.argument("thing_uuid")
@click.argument("parameters")
@click.argument("target_uri")
def main(thing_uuid: str, parameters: str, target_uri: str):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    params = json.loads(parameters.replace("'", '"'))

    resolution = params["time_resolution"]
    station_id = params["station_id"]

    datastream_id = get_datastream(uri=target_uri, thing_uuid=thing_uuid)
    start_date = get_latest_observation(uri=target_uri, datastream_id=datastream_id)
    parsed_observations = get_nm_station_data(
        station=station_id,
        resolution=resolution,
        start_date=start_date,
        end_date=datetime.now(),
    )

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
        f"observations for thing {thing_uuid} from NM API into TimeIO DB"
    )
    mqtt.publish_single("data_parsed", json.dumps({"thing_uuid": thing_uuid}))


if __name__ == "__main__":
    main()
