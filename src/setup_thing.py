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
from setup_grafana_dashboard import CreateThingInGrafanaHandler
from setup_frost import CreateFrostInstanceHandler
from setup_crontab import CreateThingInCrontabHandler

logger = logging.getLogger("thing-setup")


class SetupThingHandler(AbstractHandler):
    """Consolidated handler that orchestrates multiple setup actions"""

    HANDLERS = {
        "database": CreateThingInPostgresHandler,
        "minio": CreateThingInMinioHandler,
        "mqtt": CreateMqttUserHandler,
        "grafana": CreateThingInGrafanaHandler,
        "frost": CreateFrostInstanceHandler,
        "crontab": CreateThingInCrontabHandler,
    }

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

        # Initialize only the requested handlers
        self.handlers = []
        for action in actions:
            if action not in self.HANDLERS:
                raise ValueError(f"Unknown action: {action}")
            handler_class = self.HANDLERS[action]
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
    all_actions = list(SetupThingHandler.HANDLERS.keys())

    parser = argparse.ArgumentParser(
        description="Consolidated thing setup handler - orchestrates multiple setup actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available actions:
  database   Setup PostgreSQL user/schema/tables
  minio      Setup MinIO user/bucket/policy
  mqtt       Setup MQTT user
  grafana    Setup Grafana dashboard
  frost      Setup FROST-Server instance
  crontab    Setup crontab entry

Examples:
  # Run all setup actions (default order)
  python setup_thing.py
  python setup_thing.py all
  
  # Run only database and MinIO setup
  python setup_thing.py database minio
  
  # Custom order
  python setup_thing.py crontab frost database
        """,
    )

    parser.add_argument(
        "actions",
        nargs="*",
        choices=all_actions + ["all"],
        help="Setup actions to perform (in order). Use 'all' or omit to run all actions. Available: %(choices)s",
    )

    args = parser.parse_args()

    # Handle "all" or no arguments -> run all actions
    if not args.actions or args.actions == ["all"]:
        actions = all_actions
    else:
        actions = args.actions

    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    logger.info(f"Starting consolidated handler with actions: {', '.join(actions)}")

    handler = SetupThingHandler(actions)
    handler.run_loop()


if __name__ == "__main__":
    main()
