import requests
import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload

logger = logging.getLogger("bento-setup")


class CreateThingInBentoHandler(AbstractHandler):

    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )

        self.configdb_dsn = get_envvar("CONFIGDB_DSN")
        self.bento_api_url = get_envvar("BENTO_API_URL")
        self.bento_api_url_POST = get_envvar("BENTO_API_URL_POST")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)

        # Prepare Bento stream configuration
        stream_config = self.prepare_stream_config(thing)

        # Create or update the Bento stream
        self.create_or_update_stream(stream_config, thing)

    def prepare_stream_config(self, thing: Thing):
        ingest_type_id = thing.ingest_type_id
        path = thing.url_for_thing if thing.url_for_thing else thing.uuid
        bento_timestamp = "${!now().ts_format(\"1_Jan_2006_15:04:05\")}"

        # Create Bento stream configuration
        if ingest_type_id == "5":
            stream_config = {
                "input": {
                    "mqtt": {
                        "urls": [f"tcp://{thing.ext_mqtt.external_mqtt_address}:{thing.ext_mqtt.external_mqtt_port}"],
                        "client_id": "",
                        "dynamic_client_id_suffix": "",
                        "connect_timeout": "30s",
                        "will": {
                            "enabled": False,
                            "qos": 0,
                            "retained": False,
                            "topic": "",
                            "payload": ""
                        },
                        "user": thing.ext_mqtt.external_mqtt_username,
                        "password": thing.ext_mqtt.external_mqtt_password,
                        "keepalive": 30,
                        "tls": {
                            "enabled": False,
                            "skip_cert_verify": False,
                            "enable_renegotiation": False,
                            "root_cas": thing.ext_mqtt.external_mqtt_ca_cert,
                            "root_cas_file": "",
                            "client_certs": [
                                {
                                    "cert": thing.ext_mqtt.external_mqtt_client_cert,
                                    "key": thing.ext_mqtt.external_mqtt_client_key,
                                }
                            ]
                        },
                        "topics": [thing.ext_mqtt.external_mqtt_topic],
                        "qos": 1,
                        "clean_session": True,
                        "auto_replay_nacks": True
                    }
                },
                "pipeline": {
                    "processors": [
                        {
                            "bloblang": "root = content()"
                        }
                    ]
                },
                "output": {
                    "mqtt": {
                        "urls": ["mqtt-broker:1883"],
                        "user": thing.mqtt.user,
                        "password": thing.mqtt.password,
                        "topic": f"mqtt_ingest/{thing.mqtt.user}"
                    }
                }
            }

        elif ingest_type_id == "6":
            stream_config = {
                "input": {
                    "http_server": {
                        "address": "",  # or configurable
                        "path": f"/http-ingest/{path}",
                        "ws_path": f"/http-ingest/{path}/ws",
                        "allowed_verbs": ["POST"],
                        "timeout": "5s",
                        "rate_limit": ""
                    }
                },
                "buffer": {
                    "type": "none"
                },
                "pipeline": {
                    "processors": [
                        {
                            "mapping": "root = content()"
                        }
                    ]
                },
                "output": {
                    "aws_s3": {
                        "bucket": f"{thing.s3_store.bucket}",
                        "path": f"{bento_timestamp}.{thing.ext_http.file_type}",
                        "endpoint": "http://object-storage:9000",
                        "force_path_style_urls": True,
                        "region": "",
                        "credentials": {
                            "id": f"{thing.s3_store.user}",  # ideally inject via env/config
                            "secret": f"{thing.s3_store.password}"
                        }
                    }
                }
            }
        else:
            raise ValueError(f"Unsupported ingest_type_id: {ingest_type_id}")
        return stream_config

    def create_or_update_stream(self, stream_config, thing: Thing):
        """Create or update a Bento stream via JSON API"""
        url = f"{self.bento_api_url_POST}/streams/mqtt/{thing.uuid}"

        try:
            # First try to get existing stream
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                # Stream exists, update it
                logger.info(f"Updating existing stream: {thing.uuid}")
                response = requests.put(url,
                                        json=stream_config,
                                        timeout=30)
            else:
                # Stream doesn't exist, create it
                logger.info(f"Creating new stream: {thing.uuid}")
                response = requests.post(url,
                                         json=stream_config,
                                         timeout=30)

            if response.ok:
                logger.info(f"Successfully configured stream: {thing.uuid}")
            else:
                logger.error(f"Failed to configure stream {thing.uuid}: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error configuring Bento stream: {e}")

if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInBentoHandler().run_loop()
