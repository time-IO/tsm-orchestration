#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging

import requests
import click

import tsm_datastore_lib
from tsm_datastore_lib.Observation import Observation


def cleanupJson(string: str) -> str:
    """
    The json string from the TTN Endpoint is erroneous
    and not directly parsable -> remove excess comas
    """
    rep = ",".join(filter(None, string.split("\n")))
    return f"[{rep}]".strip()


@click.command()
@click.argument("thing_uuid")
@click.argument("parameters")
@click.argument("target_uri")
def main(thing_uuid: str, parameters: str, target_uri: str):
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    params = json.loads(parameters.replace("'", '"'))

    res = requests.get(
        params["endpoint_uri"],
        headers={
            "Authorization": f"Bearer {params['api_key']}",
            "Accept": "text/event-stream",
        },
    )

    rep = cleanupJson(res.text)
    payload = json.loads(rep)

    observations = []
    for entry in payload:
        msg = entry["result"]["uplink_message"]
        timestamp = msg["received_at"]
        values = msg["decoded_payload"]
        for i, (k, v) in enumerate(values.items()):
            if i == 1:
                break
            if v:
                try:
                    observations.append(
                        Observation(
                            timestamp=timestamp,
                            value=float(v),
                            origin=params["endpoint_uri"],
                            position=k,
                            header=k,
                        )
                    )
                except Exception as e:
                    logging.warning(
                        f"failed to integrate key '{k}' at timestamp '{timestamp}' with exception {e}"
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
