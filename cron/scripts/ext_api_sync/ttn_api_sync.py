#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging

import requests
import click
import mqtt

from decrypt import decrypt

api_base_url = os.environ.get("DB_API_BASE_URL")


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
    api_key_dec = decrypt(params["api_key"])

    res = requests.get(
        params["endpoint_uri"],
        headers={
            "Authorization": f"Bearer {api_key_dec}",
            "Accept": "text/event-stream",
        },
    )

    rep = cleanupJson(res.text)
    payload = json.loads(rep)

    bodies = []
    for entry in payload:
        msg = entry["result"]["uplink_message"]
        timestamp = msg["received_at"]
        values = msg["decoded_payload"]
        for k, v in values.items():
            if v:
                body = {
                    "result_time": timestamp,
                    "result_type": 0,
                    "datastream_pos": k,
                    "result_number": float(v),
                    "parameters": json.dumps(
                        {"origin": params["endpoint_uri"], "column_header": k}
                    ),
                }
                bodies.append(body)
    post_data = {"observations": bodies}

    resp = requests.post(
        f"{api_base_url}/observations/upsert/{thing_uuid}",
        json=post_data,
        headers={"Content-type": "application/json"},
    )
    if resp.status_code != 201:
        logging.error(f"{resp.text}")
        resp.raise_for_status()
        # exit

    logging.info(
        f"Successfully inserted {len(post_data['observations'])} "
        f"observations for thing {thing_uuid} from TTN API into TimeIO DB"
    )
    mqtt.send_mqtt_info("data_parsed", json.dumps({"thing_uuid": thing_uuid}))


if __name__ == "__main__":
    main()
