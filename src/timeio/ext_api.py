import requests
import json
import base64
import re

from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

from timeio.feta import Thing
from timeio.mqtt import publish_single
from timeio.typehints import MqttPayload
from timeio.crypto import decrypt, get_crypt_key


class NoHttpsError(Exception):
    def __init_(self, msg):
        super().__init__(msg)


RESULT_TYPE_MAPPING = {
    0: "result_number",
    1: "result_string",
    2: "result_json",
    3: "result_boolean",
}


class BoschApiSyncer:
    PARAMETER_MAPPING = {
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

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
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
                        RESULT_TYPE_MAPPING[result_type]: value,
                        "parameters": json.dumps(
                            {"origin": "bosch_data", "column_header": source}
                        ),
                    }
                    bodies.append(body)
        return {"observations": bodies}


class TsystemsApiSyncer:
    tsystems_base_url = (
        "https://moc.caritc.de/sensorstation-management/api/measurements/average"
    )
    tsytems_auth_url = (
        "https://lcmm.caritc.de/auth/realms/lcmm/protocol/openid-connect/token"
    )

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
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


class UbaApiSyncer:
    uba_componsents_url = (
        "https://www.umweltbundesamt.de/api/air_data/v3/components/json"
    )
    uba_scopes_url = "https://www.umweltbundesamt.de/api/air_data/v3/scopes/json"
    uba_limits_url = "https://www.umweltbundesamt.de/api/air_data/v3/measures/limits"
    uba_measures_url = "https://www.umweltbundesamt.de/api/air_data/v3/measures/json"
    uba_airquality_url = (
        "https://www.umweltbundesamt.de/api/air_data/v3/airquality/json"
    )

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
        settings = thing.ext_api.settings
        station_id = settings["station_id"]
        date_from, time_from, date_to, time_to = self.parse_timeranges(
            content["datetime_from"], content["datetime_to"]
        )
        components, scopes = self.get_components_and_scopes()
        measure_data = self.combine_measure_responses(
            station_id, date_from, date_to, time_from, time_to, components, scopes
        )
        aqi_data = self.get_airquality_data(
            station_id, date_from, date_to, time_from, time_to, components
        )
        parsed_measure_data = self.parse_measure_data(measure_data, station_id)
        parsed_aqi_data = self.parse_aqi_data(aqi_data, station_id)
        return {"observations": parsed_measure_data + parsed_aqi_data}

    @staticmethod
    def parse_timeranges(dt_from_str, dt_to_str):
        dt_from = datetime.strptime(dt_from_str, "%Y-%m-%d %H:%M:%S")
        dt_to = datetime.strptime(dt_to_str, "%Y-%m-%d %H:%M:%S")
        date_from = dt_from.date().strftime("%Y-%m-%d")
        time_from = dt_from.hour
        date_to = dt_to.date().strftime("%Y-%m-%d")
        time_to = dt_to.hour
        return date_from, time_from, date_to, time_to

    @staticmethod
    def adjust_datetime(datetime_str: str) -> str:
        """UBA API returns datetime format with hours from 1 to 24 so it
        has to be parsed for timeIO DB API
        """
        date = datetime.strptime(datetime_str[0:10], "%Y-%m-%d")
        date_adjusted = date + timedelta(days=1)

        return date_adjusted.strftime("%Y-%m-%d %H:%M:%S")

    def get_components_and_scopes(self):
        """Get components (i.e measured quantites) and scopes
        (aggregation infos) for later mapping
        """
        response_components = requests.get(self.uba_componsents_url)
        response_components.raise_for_status()
        response_scopes = requests.get(self.uba_scopes_url)
        response_scopes.raise_for_status()
        components = {
            int(v[0]): v[1]
            for k, v in response_components.json().items()
            if k not in ["count", "indices"]
        }
        scopes = {
            int(v[0]): v[1]
            for k, v in response_scopes.json().items()
            if k not in ["count", "indices"]
        }
        return components, scopes

    def get_station_info(self, station_id: str) -> list:
        """Get all available components and scope combinations of a given
        station
        """
        station_info = list()
        response = requests.get(self.uba_limits_url)
        response.raise_for_status()
        response_json = response.json()["data"]
        for k, v in response_json.items():
            if v[2] == station_id:
                station_info.append({"scope": int(v[0]), "component": int(v[1])})
        return station_info

    def request_measure_endpoint(
        self,
        station_id: str,
        component_id: int,
        scope_id: int,
        date_from: str,
        date_to: str,
        time_from: int,
        time_to: int,
    ) -> dict:
        """Request uba api measure endpoint for a given component and scope
        and a given time range
        """
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "time_from": time_from,
            "time_to": time_to,
            "station": station_id,
            "component": component_id,
            "scope": scope_id,
        }
        response = requests.get(
            url=self.uba_measures_url,
            params=params,
        )
        response.raise_for_status()
        response_json = response.json()
        if response_json["data"]:
            return response_json["data"][station_id]
        else:
            return response_json["data"]

    def combine_measure_responses(
        self,
        station_id: str,
        date_from: str,
        date_to: str,
        time_from: int,
        time_to: int,
        components: dict,
        scopes: dict,
    ) -> list:
        """Combine uba respones for all component/scope combinations into
        one object
        """
        measure_data = list()
        station_info = self.get_station_info(station_id)
        for entry in station_info:
            response = self.request_measure_endpoint(
                station_id,
                entry["component"],
                entry["scope"],
                date_from,
                date_to,
                time_from,
                time_to,
            )
            for k, v in response.items():
                measure_data.append(
                    {
                        "timestamp": v[3],
                        "value": v[2],
                        "measure": f"{components[entry['component']]} {scopes[entry['scope']]}",
                    }
                )
        return measure_data

    def parse_measure_data(self, measure_data: list, station_id: str) -> list:
        """Creates POST body from combined uba measures data"""
        bodies = []
        source = {
            "uba_station_id": station_id,
            "endpoint": "/measures",
        }
        for entry in measure_data:
            if entry["timestamp"][11:13] == "24":
                entry["timestamp"] = self.adjust_datetime(entry["timestamp"])
            if entry["value"]:
                body = {
                    "result_time": entry["timestamp"],
                    "result_type": 0,
                    "result_number": entry["value"],
                    "datastream_pos": entry["measure"],
                    "parameters": json.dumps(
                        {"origin": "uba_data", "column_header": source}
                    ),
                }
                bodies.append(body)
        return bodies

    def get_airquality_data(
        self,
        station_id: str,
        date_from: str,
        date_to: str,
        time_from: int,
        time_to: int,
        components: dict,
    ) -> list:
        """Request uba api airquality endpoint for a given station_id and
        time range
        """
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "time_from": time_from,
            "time_to": time_to,
            "station": station_id,
        }
        response = requests.get(self.uba_airquality_url, params=params)
        response.raise_for_status()
        response_json = response.json()
        if not response_json["data"]:
            return []

        response_data = response_json["data"][station_id]
        aqi_data = []
        for k, v in response_data.items():
            pollutant_info = list()
            for i in range(3, len(v)):
                entry = {"component": components[v[i][0]], "airquality_index": v[i][2]}
                pollutant_info.append(entry)
            aqi_data.append(
                {
                    "timestamp": v[0],
                    "airquality_index": v[1],
                    "data_complete": v[2],
                    "pollutant_info": pollutant_info,
                }
            )
        return aqi_data

    def parse_aqi_data(self, aqi_data: list, station_id: str) -> list:
        """Creates POST body from uba air quality data"""
        bodies = []
        for entry in aqi_data:
            source = {
                "uba_station_id": station_id,
                "endpoint": "/airquality",
                "pollutant_info": entry["pollutant_info"],
            }
            if entry["timestamp"][11:13] == "24":
                entry["timestamp"] = self.adjust_datetime(entry["timestamp"])
            if entry["airquality_index"]:
                body = {
                    "result_time": entry["timestamp"],
                    "result_type": 0,
                    "result_number": entry["airquality_index"],
                    "datastream_pos": "AQI",
                    "parameters": json.dumps(
                        {"origin": "uba_data", "column_header": source}
                    ),
                }
                bodies.append(body)
        return bodies


class DwdApiSyncer:
    PARAMETER_MAPPING = {
        "cloud_cover": 0,
        "condition": 1,
        "dew_point": 0,
        "icon": 1,
        "precipitation": 0,
        "precipitation_probability": 0,
        "precipitation_probability_6h": 0,
        "pressure_msl": 0,
        "relative_humidity": 0,
        "solar": 0,
        "sunshine": 0,
        "temperature": 0,
        "visibility": 0,
        "wind_direction": 0,
        "wind_speed": 0,
        "wind_gust_direction": 0,
        "wind_gust_speed": 0,
    }
    brightsky_base_url = "https://api.brightsky.dev/weather"

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
        settings = thing.ext_api.settings
        response = self.fetch_brightsky_data(
            settings["station_id"], content["datetime_from"], content["datetime_to"]
        )
        parsed_observations = self.parse_brightsky_response(response)
        return parsed_observations

    def fetch_brightsky_data(self, station_id: str, dt_from: str, dt_to: str) -> dict:
        """Returns DWD data with hourly resolution of yesterday"""
        params = {
            "dwd_station_id": station_id,
            "date": dt_from,
            "last_date": dt_to,
            "units": "dwd",
        }
        brightsky_response = requests.get(url=self.brightsky_base_url, params=params)
        response_data = brightsky_response.json()
        return response_data

    def parse_brightsky_response(self, resp) -> dict:
        """Uses Brightsky Response and returns body for POST request"""
        observation_data = resp["weather"]
        source = resp["sources"][0]
        bodies = []
        for obs in observation_data:
            timestamp = obs.pop("timestamp")
            del obs["source_id"]
            for parameter, value in obs.items():
                if value:
                    result_type = self.PARAMETER_MAPPING[parameter]
                    body = {
                        "result_time": timestamp,
                        "result_type": result_type,
                        "datastream_pos": parameter,
                        RESULT_TYPE_MAPPING[result_type]: value,
                        "parameters": json.dumps(
                            {"origin": "dwd_data", "column_header": source}
                        ),
                    }
                    bodies.append(body)
        return {"observations": bodies}


class TtnApiSyncer:
    PARAMETER_MAPPING = {
        "BAT": 0,
        "H1": 0,
        "H2": 0,
        "InputStatus": 1,
        "T1": 0,
        "Work_mode": 1,
    }

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
        settings = thing.ext_api.settings
        api_key_dec = decrypt(settings["api_key"], get_crypt_key())
        url = settings["endpoint_uri"]
        ttn_payload = self.fetch_ttn_data(url, api_key_dec)
        parsed_observations = self.parse_ttn_response(ttn_payload, url)
        return parsed_observations

    def fetch_ttn_data(self, url, api_key):
        res = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/event-stream",
            },
        )

        rep = self.cleanup_json(res.text)
        return json.loads(rep)

    def parse_ttn_response(self, payload, url):
        bodies = []
        for entry in payload:
            msg = entry["result"]["uplink_message"]
            timestamp = msg["received_at"]
            values = msg["decoded_payload"]
            for k, v in values.items():
                if v:
                    result_type = self.PARAMETER_MAPPING[k]
                    body = {
                        "result_time": timestamp,
                        "result_type": result_type,
                        "datastream_pos": k,
                        RESULT_TYPE_MAPPING[result_type]: v,
                        "parameters": json.dumps({"origin": url, "column_header": k}),
                    }
                    bodies.append(body)
        return {"observations": bodies}

    @staticmethod
    def cleanup_json(string: str) -> str:
        """
        The json string from the TTN Endpoint is erroneous
        and not directly parsable -> remove excess comas
        """
        rep = ",".join(filter(None, string.split("\n")))
        return f"[{rep}]".strip()


class NmApiSyncer:
    nm_base_url = "http://www.nmdb.eu/nest/draw_graph.php"

    def parse(self, thing: Thing, content: MqttPayload.SyncExtApiT):
        settings = thing.ext_api.settings
        station_id = settings["station_id"]
        resolution = settings["time_resolution"]
        start_date = datetime.strptime(content["datetime_from"], "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(content["datetime_to"], "%Y-%m-%d %H:%M:%S")
        nm_response = self.fetch_nm_data(station_id, resolution, start_date, end_date)
        parsed_observations = self.parse_nm_response(
            nm_response, station_id, resolution
        )
        return parsed_observations

    def fetch_nm_data(
        self, station: str, resolution: int, start_date: datetime, end_date: datetime
    ) -> list:
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
        res = requests.get(self.nm_base_url, params=params)
        rows = [
            r.split(";") for r in re.findall(r"^\d.*", res.text, flags=re.MULTILINE)
        ]
        return rows

    def parse_nm_response(self, resp, station, resolution) -> dict:
        bodies = []
        header = {
            "sensor_id": station,
            "resolution": resolution,
            "nm_api_url": self.nm_base_url,
        }
        for timestamp, value in resp:
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
