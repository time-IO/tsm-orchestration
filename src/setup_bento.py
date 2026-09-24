import json
import requests
import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload
from timeio.crypto import decrypt, get_crypt_key

logger = logging.getLogger("bento-setup")

BENTO_INGEST_TYPES = ("external_mqtt", "http")


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

        self.dsmdb_dsn = get_envvar("DSMDB_DSN")
        self.bento_api_url = get_envvar("BENTO_API_URL")
        self.bento_api_url_POST = get_envvar("BENTO_API_URL_POST")
        self.s3_region = get_envvar("S3_REGION")
        self.crypt_key = get_crypt_key()

    def act(self, content: MqttPayload.UpdateThing, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.dsmdb_dsn)
        # thing.ingest_type is a timeio.feta.IngestType wrapper object, not a
        # plain str -- .name holds the actual "external_mqtt"/"http"/... value.
        ingest_type = thing.ingest_type.name
        logger.info(
            f"Received update for thing {thing.uuid} ({thing.name}), "
            f"ingest_type={ingest_type}"
        )

        # Only act for "Bento"-Ingests
        if ingest_type not in BENTO_INGEST_TYPES:
            logger.info(
                f"Skipping {thing.uuid}: ingest_type {ingest_type!r} is not "
                f"Bento-managed ({BENTO_INGEST_TYPES})"
            )
            return

        ingest = thing.http if ingest_type == "http" else thing.ext_mqtt
        if ingest is None:
            logger.warning(
                f"Skipping {thing.uuid}: no {ingest_type} ingest details "
                f"found for this thing"
            )
            return

        if ingest.enabled:
            logger.info(
                f"Ingest {thing.uuid} is enabled, preparing Bento stream config"
            )
            try:
                stream_config = self.prepare_stream_config(thing, ingest_type)
            except Exception as e:
                logger.error(
                    f"Failed to prepare Bento stream config for {thing.uuid}: {e}"
                )
                return
            self.create_or_update_stream(stream_config, thing, ingest_type)
        else:
            logger.info(
                f"Ingest {thing.uuid} is disabled, ensuring its Bento stream is removed"
            )
            self.delete_stream(thing, ingest_type)

    def dec(self, v):
        # feta reads raw DB columns, so encrypted fields need decrypting here.
        return decrypt(v, self.crypt_key) if v else v

    def prepare_stream_config(self, thing: Thing, ingest_type: str):
        # fmt: off
        bento_timestamp = "${!now().ts_format(\"20060102_150405\")}"

        # Create Bento stream configuration
        if ingest_type == "external_mqtt":
            ca_cert = self.dec(thing.ext_mqtt.external_mqtt_ca_cert)
            client_cert = self.dec(thing.ext_mqtt.external_mqtt_client_cert)
            client_key = self.dec(thing.ext_mqtt.external_mqtt_client_key)
            ext_password = self.dec(thing.ext_mqtt.external_mqtt_password)
            # No TLS toggle in the schema; infer it from port 8883 or a cert being set.
            tls_enabled = thing.ext_mqtt.external_mqtt_port == 8883 or bool(ca_cert) or bool(client_cert)
            stream_config = {
                "input": {
                    "mqtt": {
                        "urls": [f"tcp://{thing.ext_mqtt.external_mqtt_address}:{thing.ext_mqtt.external_mqtt_port}"],
                        # empty client_id gets "identifier rejected" by most brokers
                        "client_id": f"timeio-ext-{thing.uuid}",
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
                        "password": ext_password,
                        "keepalive": 30,
                        "tls": {
                            "enabled": tls_enabled,
                            "skip_cert_verify": False,
                            "enable_renegotiation": False,
                            "root_cas": ca_cert or "",
                            "root_cas_file": "",
                            "client_certs": (
                                [{"cert": client_cert, "key": client_key}]
                                if client_cert and client_key else []
                            )
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
                        "client_id": f"timeio-int-{thing.uuid}",
                        "user": thing.mqtt.user,
                        "password": self.dec(thing.mqtt.password),
                        "topic": f"mqtt_ingest/{thing.mqtt.user}"
                    }
                }
            }
            logger.info(
                f"Prepared ExtMQTT stream for {thing.uuid}: "
                f"source={thing.ext_mqtt.external_mqtt_address}:{thing.ext_mqtt.external_mqtt_port} "
                f"topic={thing.ext_mqtt.external_mqtt_topic!r} -> "
                f"internal topic mqtt_ingest/{thing.mqtt.user}"
            )

        elif ingest_type == "http":
            path = thing.http.path_for_posts if thing.http.path_for_posts else thing.uuid
            api_key = self.dec(thing.http.api_key)

            http_server = {
                "address": "",  # or configurable
                "path": f"/http-ingest/{path}",
                "ws_path": f"/http-ingest/{path}/ws",
                "allowed_verbs": ["POST"],
                "timeout": "5s",
                "rate_limit": ""
            }
            aws_s3_output = {
                "aws_s3": {
                    "bucket": f"{thing.s3_store.bucket}",
                    "path": f"{bento_timestamp}.{thing.http.file_type}",
                    "endpoint": "http://object-storage:9000",
                    "force_path_style_urls": True,
                    "region": self.s3_region,
                    "credentials": {
                        "id": f"{thing.s3_store.user}",  # ideally inject via env/config
                        "secret": self.dec(thing.s3_store.password)
                    }
                }
            }

            if api_key:
                # Require a matching X-Api-Key header. Unauthorized requests
                # get a 401 and are never written to the bucket.
                http_server["sync_response"] = {
                    "status": '${! meta("status_code") }',
                    "headers": {"Content-Type": "application/json"}
                }
                processors = [{
                    "mapping": (
                        f'let ok = meta("X-Api-Key") == {json.dumps(api_key)}\n'
                        'meta status_code = if $ok { "200" } else { "401" }\n'
                        'root = if $ok { content() } else { {"error": "unauthorized"} }'
                    )
                }]
                output = {
                    "switch": {
                        "cases": [
                            {
                                "check": 'meta("status_code") == "200"',
                                "output": {
                                    "broker": {
                                        "pattern": "fan_out",
                                        "outputs": [{"sync_response": {}}, aws_s3_output]
                                    }
                                }
                            },
                            {"check": "", "output": {"sync_response": {}}}
                        ]
                    }
                }
            else:
                processors = [{"mapping": "root = content()"}]
                output = aws_s3_output

            stream_config = {
                "input": {"http_server": http_server},
                "buffer": {"type": "none"},
                "pipeline": {"processors": processors},
                "output": output
            }
            logger.info(
                f"Prepared HTTP stream for {thing.uuid}: "
                f"path=/http-ingest/{path} -> bucket={thing.s3_store.bucket} "
                f"(api_key {'required' if api_key else 'not set'})"
            )
        else:
            raise ValueError(f"Unsupported ingest_type: {ingest_type}")
        return stream_config

    # fmt: on

    def create_or_update_stream(self, stream_config, thing: Thing, ingest_type: str):
        """Create or update a Bento stream via JSON API"""
        url = f"{self.bento_api_url_POST}/streams/{ingest_type}/{thing.uuid}"
        # bento_api_url_POST only accepts POST/PUT/DELETE; check existence via the real API.
        exists_url = f"{self.bento_api_url}/streams/{thing.uuid}"

        try:
            # First try to get existing stream
            response = requests.get(exists_url, timeout=30)

            if response.status_code == 200:
                # Stream exists, update it
                logger.info(f"Updating existing stream: {thing.uuid} at {url}")
                response = requests.put(url, json=stream_config, timeout=30)
            else:
                # Stream doesn't exist, create it
                logger.info(f"Creating new stream: {thing.uuid} at {url}")
                response = requests.post(url, json=stream_config, timeout=30)

            if response.ok:
                logger.info(
                    f"Successfully configured stream: {thing.uuid} "
                    f"(status {response.status_code})"
                )
            else:
                logger.error(
                    f"Failed to configure stream {thing.uuid}: {response.status_code} - {response.text}"
                )

        except Exception as e:
            logger.error(f"Error configuring Bento stream {thing.uuid} at {url}: {e}")

    def delete_stream(self, thing: Thing, ingest_type: str):
        """Delete Bento stream if it exists, otherwise log nothing to do."""

        url = f"{self.bento_api_url_POST}/streams/{ingest_type}/{thing.uuid}"
        exists_url = (
            f"{self.bento_api_url}/streams/{thing.uuid}"  # see create_or_update_stream
        )

        try:
            # Check existence first
            head = requests.get(exists_url, timeout=30)

            if head.status_code == 200:
                # Stream exists -> delete it
                del_resp = requests.delete(url, timeout=30)
                if del_resp.ok or del_resp.status_code in (202, 204):
                    logger.info(f"Disabled existing stream: {thing.uuid}")
                else:
                    logger.error(
                        f"Failed to disable stream {thing.uuid}: "
                        f"{del_resp.status_code} - {del_resp.text}"
                    )
            else:
                logger.info(f"Nothing to disable, not active yet {thing.uuid}")

        except Exception as e:
            logger.error(f"Error disabling Bento stream {thing.uuid}: {e}")


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInBentoHandler().run_loop()
