import requests
import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar
from timeio.typehints import MqttPayload

logger = logging.getLogger("")


class CreateBentoMQTTHandler(AbstractHandler):

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

        self.bento_api_url = "http://bento:4195"
        self.bento_api_url_POST = "http://bento:4200"

    def prepare_stream_config(self, content: , message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"])

        # Create Bento stream configuration
        stream_config = {
            "name": f"thing-{thing.uuid}",
            "input": {
                "mqtt": {
                    "url": self.config["mqtt_broker"],
                    "client_id": self.config["mqtt_client_id"],
                    "username": self.config["mqtt_user"],
                    "password": self.config["mqtt_password"],
                    "topics": [self.config["topic"]]
                }
            },
            "pipeline": {
                "processors": [
                    {
                        "bloblang": f'''root = content()'''
                    }
                ]
            },
            "output": {
                "mqtt": {
                    "url": self.config["mqtt_broker"],
                    "username": self.config["mqtt_user"],
                    "password": self.config["mqtt_password"],
                    "topic": [self.config["topic"]]
                }
            }
        }

        # Create or update the Bento stream
        self.create_or_update_stream(stream_config)

    def create_or_update_stream(self, stream_config):
        """Create or update a Bento stream via JSON API"""
        stream_name = stream_config["name"]
        url = f"{self.bento_api_url_POST}/streams/{stream_name}"

        try:
            # First try to get existing stream
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                # Stream exists, update it
                logger.info(f"Updating existing stream: {stream_name}")
                response = requests.put(url,
                                        json=stream_config,
                                        timeout=30)
            else:
                # Stream doesn't exist, create it
                logger.info(f"Creating new stream: {stream_name}")
                response = requests.post(url,
                                         json=stream_config,
                                         timeout=30)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully configured stream: {stream_name}")
            else:
                logger.error(f"Failed to configure stream {stream_name}: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error configuring Bento stream: {e}")

    def delete_stream(self, stream_name):
        """Delete a Bento stream"""
        url = f"{self.bento_api_url}/streams/{stream_name}"
        try:
            response = requests.delete(url, timeout=30)
            if response.status_code == 200:
                logger.info(f"Successfully deleted stream: {stream_name}")
            else:
                logger.error(f"Failed to delete stream {stream_name}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error deleting Bento stream: {e}")
