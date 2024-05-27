import requests
import sys
import os
import logging

from ast import literal_eval
from datetime import datetime, timedelta
from typing import cast

import tsm_datastore_lib
from tsm_datastore_lib import SqlAlchemyDatastore
from tsm_datastore_lib.Observation import Observation


thing_uuid = sys.argv[1]
properties = literal_eval(sys.argv[2])
target_uri = sys.argv[3]
brightsky_base_url = "https://api.brightsky.dev/weather"


def fetch_brightsky_data() -> dict:
    """ Returns DWD data with hourly resolution of yesterday"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_start = datetime.strftime(yesterday, '%Y-%m-%d:00:00:00')
    yesterday_end = datetime.strftime(yesterday, '%Y-%m-%d:23:55:00')
    params = {"dwd_station_id": properties["station_id"],
              "date": yesterday_start,
              "last_date": yesterday_end,
              "units": "dwd"}
    response = requests.get(url=brightsky_base_url, params=params)
    response_data = response.json()

    return response_data


def parse_brighstky_response(origin: str) -> list[Observation]:
    """ Parses Brightsky response and returns list of tsm-datastore-lib Observations"""
    payload = fetch_brightsky_data()
    observation_data = payload["weather"]
    source = payload["sources"][0]
    out = []

    for obs in observation_data:
        timestamp = obs.pop("timestamp")
        timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
        del obs["source_id"]
        for parameter, value in obs.items():
            try:
                entry = Observation(
                    timestamp=timestamp,
                    value=value,
                    position=parameter,
                    origin=origin,
                    header=source,
                )
            except Exception as e:
                continue
            out.append(entry)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    observation_list = parse_brighstky_response("dwd_data")
    datastore = tsm_datastore_lib.get_datastore(target_uri, thing_uuid)
    datastore = cast(SqlAlchemyDatastore, datastore)
    try:
        datastore.store_observations(observation_list)
        datastore.insert_commit_chunk()
    except Exception:
        datastore.session.rollback()
        raise
