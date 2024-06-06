#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
from datetime import datetime

import requests
import psycopg

import tsm_datastore_lib
from tsm_datastore_lib.Observation import Observation

URL = "http://www.nmdb.eu/nest/draw_graph.php"

URI = "postgresql://ufztimese_demogroup_656c65d5c8df47e9a02f51e26f8f9f40:G9xzojdyX0Cfr3gaqgK1flcd@localhost/postgres"
THING = "6b7e0abb-7f70-4014-a5d4-665289350301"


def get_or_insert_datastreams(
    uri: str, thing_uuid: str, stations: list[str]
) -> dict[str, int]:

    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name FROM thing WHERE uuid = %s
                """,
                (thing_uuid,),
            )
            thing_id, thing_name = cur.fetchone()

            for s in stations:
                cur.execute(
                    """
                    INSERT INTO datastream(name, position, thing_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (position, thing_id) DO NOTHING
                    """,
                    (f"{thing_name}/{s}", s, thing_id),
                )
            conn.commit()
            cur.execute(
                "SELECT position, id FROM datastream WHERE position = ANY(%s) AND thing_id = %s",
                (stations, thing_id),
            )
            datastream_ids = dict(cur.fetchall())
    return datastream_ids


def get_latest_observations(
    uri: str, datastream_ids: dict[str, int]
) -> dict[str, datetime]:
    with psycopg.connect(uri) as conn:
        with conn.cursor() as cur:
            dates = {}
            for station, datastream_id in datastream_ids.items():
                cur.execute(
                    """
                    SELECT max(result_time) FROM observation WHERE datastream_id = %s
                    """,
                    (datastream_id,),
                )
            dates[station] = cur.fetchone()[0] or datetime(2000, 1, 1)
    return dates


def get_nm_station_data(
    station: str, resolution: int, start_date: datetime, end_date: datetime
) -> list[Observation]:
    start_date = datetime(2024, 1, 1)
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


def main(stations: str | list[str], resolution: int):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    if isinstance(stations, str):
        stations = [
            stations,
        ]

    datastream_ids = get_or_insert_datastreams(
        uri=URI, thing_uuid=THING, stations=stations
    )
    start_dates = get_latest_observations(uri=URI, datastream_ids=datastream_ids)

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

    datastore = tsm_datastore_lib.get_datastore(URI, THING)
    try:
        datastore.store_observations(observations)
        datastore.insert_commit_chunk()
    except Exception as e:
        datastore.session.rollback()
        logging.warning(f"failed to write data, because of {e}")
        raise


if __name__ == "__main__":
    main("JUNG", 60)
