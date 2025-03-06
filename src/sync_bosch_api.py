from __future__ import annotations

import base64
import json
import logging

from urllib.request import Request, urlopen
from timeio.crypto import decrypt, get_crypt_key
from timeio.feta import Thing
from timeio.typehints import MqttPayload
from timeio.ext_api import write_observations

logger = logging.getLogger("sync-bosch")


class SyncBoschApi:

    def __init__(self):
        self.PARAMETER_MAPPING = {
            "CO_3_CORR": 0,
            "ESP_0_RH_AVG": 0,
            "ESP_0_TEMP_AVG": 0,
            "ES_0_PRESS": 0,
            "NO2_1_CORR": 0,
            "O3_0_CORR": 0,
            "PS_0_PM10_CORR": 0,
            "PS_0_PM2P5_CORR": 0,
            "SO2_2_CORR": 0,
            "SO2_2_CORR_1hr": 0,
        }

        self.RESULT_TYPE_MAPPING = {
            0: "result_number",
            1: "result_string",
            2: "result_json",
            3: "result_boolean",
        }

    def sync(self, thing: Thing, content: MqttPayload.SyncExtApi):
        settings = thing.ext_api.settings
        pw_dec = decrypt(settings["password"], get_crypt_key())
        url = f"""{settings["endpoint"]}/{settings["sensor_id"]}/{content["datetime_from"]}/{content["datetime_to"]}"""
        response = self.make_request(url, settings["username"], pw_dec)
        parsed_observations = self.parse_api_response(response, origin="bosch_data")
        write_observations(thing, parsed_observations)

    @staticmethod
    def basic_auth(username, password):
        credential = f"{username}:{password}"
        b_encoded_credential = base64.b64encode(credential.encode("ascii")).decode(
            "ascii"
        )
        return f"Basic {b_encoded_credential}"

    def make_request(self, server_url, user, password, post_data=None):
        r = Request(server_url)
        r.add_header("Authorization", self.basic_auth(user, password))
        r.add_header("Content-Type", "application/json")
        r.add_header("Accept", "application/json")
        r_data = post_data
        r.data = r_data
        handle = urlopen(r)
        content = handle.read().decode("utf8")
        response = json.loads(content)
        return response

    def parse_api_response(self, response: list, origin: str):
        bodies = []
        for entry in response:
            obs = entry["payload"]
            source = {
                "sensor_id": obs.pop("deviceID"),
                "observation_type": obs.pop("Type"),
            }
            timestamp = obs.pop("UTC")
            for parameter, value in obs.items():
                if value:
                    result_type = self.PARAMETER_MAPPING[parameter]
                    body = {
                        "result_time": timestamp,
                        "result_type": result_type,
                        "datastream_pos": parameter,
                        self.RESULT_TYPE_MAPPING[result_type]: value,
                        "parameters": json.dumps(
                            {"origin": "bosch_data", "column_header": source}
                        ),
                    }
                    bodies.append(body)
        return {"observations": bodies}
