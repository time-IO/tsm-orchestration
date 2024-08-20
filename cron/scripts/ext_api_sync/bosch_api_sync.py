#! /usr/bin/env python3

import click
import base64
import json
import os
import logging

from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

import tsm_datastore_lib
from tsm_datastore_lib.Observation import Observation


def basic_auth(username, password):
    credential = f"{username}:{password}"
    encoded_credential = credential.encode('ascii')
    b_encoded_credential = base64.b64encode(encoded_credential)
    b_encoded_credential = b_encoded_credential.decode('ascii')
    b_auth = b_encoded_credential
    return 'Basic %s' % b_auth


def make_request(server_url, user, password, post_data=None):
    r = Request(server_url)
    auth = basic_auth(user, password)
    r.add_header('Authorization', auth)
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
    out = []
    for entry in response:
        obs = entry["payload"]
        source = {"sensor_id": obs.pop("deviceID"),
                  "observation_type": obs.pop("Type")}
        timestamp = obs.pop("UTC")
        for parameter, value in obs.items():
            try:
                observation = Observation(
                    timestamp=timestamp,
                    value=value,
                    position=parameter,
                    origin=origin,
                    header=source,
                )
            except Exception as e:
                logging.exception(f'Creation of observation with timestamp {timestamp} and parameter {parameter} failed')
                continue
            out.append(observation)
    return out


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
    observation_list = parse_api_response(response, origin="bosch_data")
    datastore = tsm_datastore_lib.get_datastore(target_uri, thing_uuid)
    try:
        datastore.store_observations(observation_list)
        datastore.insert_commit_chunk()
    except Exception as e:
        datastore.session.rollback()
        raise RuntimeError("failed to store data in database") from e


if __name__ == "__main__":
    main()
