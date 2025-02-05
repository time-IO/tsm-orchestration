from __future__ import annotations

import json
import logging
import sys
import os
import traceback
import typing
from abc import ABC, abstractmethod

import paho.mqtt.publish
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from timeio.errors import (
    UserInputError,
    DataNotFoundError,
    ParsingError,
    NoDataWarning,
)

logger = logging.getLogger("mqtt-handler")


class AbstractHandler(ABC):
    def __init__(
        self,
        topic: str,
        mqtt_broker: str,
        mqtt_user: str,
        mqtt_password: str,
        mqtt_client_id: str,
        mqtt_qos: int,
        mqtt_clean_session: bool,
    ):
        self.topic = topic
        self.mqtt_broker = mqtt_broker
        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_qos = mqtt_qos
        self.mqtt_clean_session = mqtt_clean_session
        self.mqtt_host = mqtt_broker.split(":")[0]
        self.mqtt_port = int(mqtt_broker.split(":")[1])
        self.mqtt_client = mqtt.Client(
            client_id=mqtt_client_id,
            clean_session=self.mqtt_clean_session,
        )
        self.mqtt_client.suppress_exceptions = False
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_log = self.on_log

    def run_loop(self) -> typing.NoReturn:
        logger.info(f"Setup ok, starting listening loop")
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.subscribe(self.topic, self.mqtt_qos)
        self.mqtt_client.loop_forever()

    def on_log(self, client: mqtt.Client, userdata, level, buf):
        logger.debug(f"%s: %s", level, buf)

    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        if rc == 0:
            logger.info(
                f"Connected to %r with client ID: %s",
                self.mqtt_broker,
                self.mqtt_client._client_id.decode(),
            )
            return
        logger.error(f"Failed to connect to %r, return code: %s", self.mqtt_broker, rc)

    def on_subscribe(self, client: mqtt.Client, userdata, mid, granted_qos):
        logger.info(f"Subscribed to topic {self.topic} with QoS {granted_qos[0]}")

    def on_message(self, client: mqtt.Client, userdata, message: MQTTMessage):
        logger.info(
            "\n\n======================= NEW MESSAGE ========================\n"
            f"Topic: %r, QoS: %s, Timestamp: %s",
            message.topic,
            message.qos,
            message.timestamp,
        )

        try:
            content = self._decode(message)
        except Exception:
            logger.critical(
                f"\n====================== CRITICAL ERROR ======================\n"
                f"Status: PARSING ERROR  (Decoding/parsing of payload failed)\n"
                f"Payload:\n{message.payload!r}\n"
                f"{traceback.format_exc()}"
                f"========================= SYS EXIT =========================\n",
            )
            # We exit now, because otherwise the client.on_log would print
            # the exception again (with unnecessary clutter)
            sys.exit(1)

        try:
            logger.debug(f"calling %s.act()", self.__class__.__qualname__)
            self.act(content, message)

        except (UserInputError, ParsingError):
            logger.error(
                f"\n======================== USER ERROR ========================\n"
                f"Status: ERROR  (An error because of user data or input)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"======================== USER ERROR ========================\n",
            )
            return
        except (DataNotFoundError, NoDataWarning):
            logger.error(
                f"\n======================== DATA ERROR ========================\n"
                f"Status: ERROR  (Data is missing)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"======================== DATA ERROR ========================\n",
            )
            return

        except Exception:
            logger.critical(
                f"\n====================== CRITICAL ERROR ======================\n"
                f"Status: UNHANDLED ERROR  (See exception and traceback below)\n"
                f"Content:\n{content!r}\n"
                f"{traceback.format_exc()}"
                f"========================= SYS EXIT =========================\n",
            )
            # We exit now, because otherwise the client.on_log would print
            # the exception again (with unnecessary clutter)
            sys.exit(1)

        logger.info(
            f"\n===================== PROCESSING DONE ======================\n"
            f"Status: Success  (Message was processed successfully)\n"
            f"===================== PROCESSING DONE ======================\n",
        )

    def _decode(self, message: MQTTMessage) -> typing.Any:
        """
        This decodes the message from utf-8 and also try to decode json to python
        objects. If the object is not json (e.g. plain strings or a datetime object
        like 2022-22-22T11:11:11) the object itself is returned instead.

        Parameters
        ----------
        message : MQTTMessage
            Message to decode.

        Returns
        -------
        content:
            The decoded content

        Raises
        ------
        UnicodeDecodeError
            If the raw message is not 'utf-8' encoded.
        """
        # Hint: json.loads also decodes single numeric values,
        # the constants `null`, +/-`Infinity` and `NaN`.
        decoded: str = message.payload.decode("utf-8")
        try:
            decoded = json.loads(decoded)
        except json.JSONDecodeError:
            logger.warning(
                f"Message content is not valid json. (That's ok, but unusual)"
            )
        return decoded

    @abstractmethod
    def act(self, content: typing.Any, message: MQTTMessage):
        """
        Subclasses must overwrite this function.

        The calling function will handle the following exceptions:
         - timeio.errors.ParsingError
         - timeio.errors.UserInputError
         - timeio.errors.DataNotFoundError
         - timeio.errors.NoDataWarning

         Other exceptions will lead to a system exit.
        """

        raise NotImplementedError


def _get_settings_from_env():
    try:
        _broker = os.environ["MQTT_BROKER"]
        return {
            "qos": int(os.environ["MQTT_QOS"]),
            "hostname": _broker.split(":")[0],
            "port": int(_broker.split(":")[1]),
            "client_id": os.environ["MQTT_QOS"],
            "auth": {
                "username": os.environ["MQTT_USER"],
                "password": os.environ["MQTT_PASSWORD"],
            },
        }
    except KeyError as e:
        raise EnvironmentError(f"Missing environment variable {e}")


def publish_single(topic, payload: str):
    """
    Publish a single mqtt message to a broker, then disconnect cleanly.
    """
    paho.mqtt.publish.single(**_get_settings_from_env(), topic=topic, payload=payload)

