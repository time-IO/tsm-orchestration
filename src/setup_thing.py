from __future__ import annotations

import argparse
import logging

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging
from timeio.typehints import MqttPayload

# Import individual action handlers
from setup_user_database import CreateThingInPostgresHandler
from setup_minio import CreateThingInMinioHandler
from setup_mqtt_user import CreateMqttUserHandler
from setup_grafana_user import CreateGrafanaUserHandler
from setup_grafana_dashboard import CreateThingInGrafanaHandler
from setup_frost import CreateFrostInstanceHandler
from setup_crontab import CreateThingInCrontabHandler

logger = logging.getLogger("thing-setup")


class SetupThingHandler(AbstractHandler):
    """Consolidated handler that orchestrates multiple setup actions"""

    def __init__(self, actions: list[str]):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )

        # Map action names to handler instances
        self.available_handlers = {
            "database": CreateThingInPostgresHandler,
            "minio": CreateThingInMinioHandler,
            "mqtt": CreateMqttUserHandler,
            "grafana": CreateThingInGrafanaHandler,
            "frost": CreateFrostInstanceHandler,
            "crontab": CreateThingInCrontabHandler,
        }

        # Initialize only the requested handlers
        self.handlers = []
        for action in actions:
            if action not in self.available_handlers:
                raise ValueError(f"Unknown action: {action}")
            handler_class = self.available_handlers[action]
            # Create handler but don't start its MQTT loop
            handler = handler_class.__new__(handler_class)
            handler.__init__()
            self.handlers.append((action, handler))
            logger.info(f"Registered action: {action}")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        """Process all configured actions in sequence"""
        thing_uuid = content.get("thing")
        logger.info(f"Processing thing {thing_uuid} with {len(self.handlers)} actions")

        for action_name, handler in self.handlers:
            logger.info(f"Executing action: {action_name}")
            try:
                handler.act(content, message)
                logger.info(f"✓ Completed: {action_name}")
            except Exception as e:
                logger.error(f"✗ Failed: {action_name} - {e}", exc_info=True)

                # Decide: continue with other actions or fail fast?
                # Continue with other actions
                #
                # raise  # Uncomment to fail fast


def main():
    parser = argparse.ArgumentParser(
        description="Consolidated thing setup handler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Run all setup actions
        python setup_thing.py --database --minio --mqtt --grafana --frost --crontab
        
        # Run only database and MinIO setup
        python setup_thing.py --database --minio
        
        # Custom order
        python setup_thing.py --crontab --frost --database
        """,
    )

    # Add flag for each action
    parser.add_argument(
        "--database", action="store_true", help="Setup PostgreSQL user/schema/tables"
    )
    parser.add_argument(
        "--minio", action="store_true", help="Setup MinIO user/bucket/policy"
    )
    parser.add_argument("--mqtt", action="store_true", help="Setup MQTT user")
    parser.add_argument(
        "--grafana", action="store_true", help="Setup Grafana dashboard"
    )
    parser.add_argument(
        "--frost", action="store_true", help="Setup FROST-Server instance"
    )
    parser.add_argument("--crontab", action="store_true", help="Setup crontab entry")

    args = parser.parse_args()

    # Collect actions in the order they appear in sys.argv
    import sys

    actions = []
    action_flags = {
        "--database": "database",
        "--minio": "minio",
        "--mqtt": "mqtt",
        "--grafana": "grafana",
        "--frost": "frost",
        "--crontab": "crontab",
    }

    for arg in sys.argv[1:]:
        if arg in action_flags and getattr(args, arg.lstrip("--").replace("-", "_")):
            actions.append(action_flags[arg])

    if not actions:
        parser.error("At least one action must be specified")

    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    logger.info(f"Starting consolidated handler with actions: {', '.join(actions)}")

    handler = SetupThingHandler(actions)
    handler.run_loop()


if __name__ == "__main__":
    main()
