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

import tsm_datastore_lib
from tsm_datastore_lib.Observation import Observation

URL = "http://www.nmdb.eu/nest/draw_graph.php"

def get_nm_station_data(
    station: str, resolution: int, start_date: datetime, end_date: datetime
) -> list[Observation]:
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
    observations = []
    for timestamp, value in rows:
        try:
            observations.append(
                Observation(
                    timestamp=datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
                    value=float(value),
                    origin=URL,
                    position=station,
                )
            )
        except Exception as e:
            logging.warning(
                f"failed to integrate data for station '{station}' at timestamp '{timestamp}' with exception {e}"
            )
    return observations


def get_datastreams(
    uri: str, thing_uuid: str, stations: list[str]
) -> dict[str, int]:

    datastream_ids = {s: None for s in stations}
    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            # TODO: join both queries
            cur.execute(
                """
                SELECT id FROM thing WHERE uuid = %s
                """,
                (thing_uuid,),
            )
            thing_id = cur.fetchone()[0]

            cur.execute(
                "SELECT position, id FROM datastream WHERE position = ANY(%s) AND thing_id = %s",
                (stations, thing_id),
            )
            datastream_ids = {**datastream_ids, **dict(cur.fetchall())}
    return datastream_ids


def get_latest_observations(
    uri: str, datastream_ids: dict[str, int]
) -> dict[str, datetime]:

    dates = {s: datetime(2000, 1, 1) for s in datastream_ids.keys()}

    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            for station, datastream_id in datastream_ids.items():
                cur.execute(
                    """
                    SELECT max(result_time) FROM observation WHERE datastream_id = %s
                    """,
                    (datastream_id,),
                )
                date = cur.fetchone()[0]
                if date:
                    dates[station] = date
    return dates


@click.command()
@click.argument("thing_uuid")
@click.argument("parameters")
@click.argument("target_uri")
def main(thing_uuid: str, parameters: str, target_uri: str):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    params = json.loads(parameters.replace("'", '"'))

    resolution = params["time_resolution"]
    stations = params["station_id"]
    if isinstance(stations, str):
        stations = [
            stations,
        ]

    datastream_ids = get_datastreams(
        uri=target_uri, thing_uuid=thing_uuid, stations=stations
    )
    start_dates = get_latest_observations(uri=target_uri, datastream_ids=datastream_ids)

    observations = []
    for station in stations:
        observations.extend(
            get_nm_station_data(
                station=station,
                resolution=resolution,
                start_date=start_dates[station],
                end_date=datetime.now(),
            )
        )

    datastore = tsm_datastore_lib.get_datastore(target_uri, thing_uuid)
    try:
        datastore.store_observations(observations)
        datastore.insert_commit_chunk()
    except Exception as e:
        datastore.session.rollback()
        logging.warning(f"failed to write data, because of {e}")
        raise


if __name__ == "__main__":
    main()
