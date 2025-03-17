import requests
import json
import base64

from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timezone

from timeio.feta import Thing
from timeio.common import get_envvar
from timeio.mqtt import publish_single
from timeio.typehints import MqttPayload
from timeio.crypto import decrypt, get_crypt_key

api_base_url = get_envvar("DB_API_BASE_URL")


class NoHttpsError(Exception):
    def __init_(self, msg):
        super().__init__(msg)


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

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApi):
        settings = thing.ext_api.settings
        pw_dec = decrypt(settings["password"], get_crypt_key())
        url = f"""{settings["endpoint"]}/{settings["sensor_id"]}/{content["datetime_from"]}/{content["datetime_to"]}"""
        if urlparse(url).scheme != "https":
            raise NoHttpsError(f"{url} is not https")
        response = self.make_request(url, settings["username"], pw_dec)
        parsed_observations = self.parse_api_response(response, origin="bosch_data")
        return parsed_observations

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


class SyncTsystemsApi:

    def __init__(self):
        self.tsystems_base_url = (
            "https://moc.caritc.de/sensorstation-management/api/measurements/average"
        )
        self.tsytems_auth_url = (
            "https://lcmm.caritc.de/auth/realms/lcmm/protocol/openid-connect/token"
        )

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApi):
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
        return parsed_observations

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
