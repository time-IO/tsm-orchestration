from __future__ import annotations

import requests
import json
import logging

from datetime import datetime, timezone

from timeio.crypto import decrypt, get_crypt_key
from timeio.feta import Thing
from timeio.typehints import MqttPayload
from timeio.ext_api import write_observations

logger = logging.getLogger("sync-tsystems")


class SyncTsystemsApi:

    def __init__(self):
        self.tsystems_base_url = (
            "https://moc.caritc.de/sensorstation-management/api/measurements/average"
        )
        self.tsytems_auth_url = (
            "https://lcmm.caritc.de/auth/realms/lcmm/protocol/openid-connect/token"
        )

    def sync(self, thing: Thing, content: MqttPayload.SyncExtApi):
        settings = thing.ext_api.settings
        pw_dec = decrypt(settings["password"], get_crypt_key())
        response = self.request_tsystems_api(
            settings["group"],
            settings["station_id"],
            settings["username"],
            pw_dec,
            content["datetime_from"],
            content["datetime_to"],
        )
        parsed_observations = self.parse_api_response(response)
        write_observations(thing, parsed_observations)

    @staticmethod
    def unix_ts_to_str(ts_unix: int) -> str:
        """Convert unix timestamp to datetime string"""
        dt = datetime.fromtimestamp(ts_unix, tz=timezone.utc)
        ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        return ts_str

    def get_bearer_token(self, username: str, password: str) -> str:
        """Get bearer token for API authentication"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "client_id": "lcmm",
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        response = requests.post(self.tsytems_auth_url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]

    def request_tsystems_api(
        self,
        group: str,
        station_id: str,
        username: str,
        password: str,
        time_from: str,
        time_to: str,
    ) -> list:
        bearer_token = self.get_bearer_token(username, password)
        headers = {"Accept": "*/*", "Authorization": f"Bearer {bearer_token}"}
        params = {
            "aggregationTime": "HOURLY",
            "aggregationValues": "ALL_FIELDS",
            "from": time_from,
            "to": time_to,
        }
        response = requests.get(
            f"{self.tsystems_base_url}/{group}/{station_id}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def parse_api_response(self, response: list) -> dict:
        bodies = []
        for entry in response:
            source = {"sensor_id": entry.pop("deviceId"), "aggregation_time": "hourly"}
            timestamp = entry.pop("timestamp")
            for parameter, value in entry.items():
                if value:
                    body = {
                        "result_time": self.unix_ts_to_str(timestamp),
                        "result_type": 0,
                        "result_number": value,
                        "datastream_pos": parameter,
                        "parameters": json.dumps(
                            {"origin": "tsystems_data", "column_header": source}
                        ),
                    }
                    bodies.append(body)
        return {"observations": bodies}
