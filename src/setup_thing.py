from __future__ import annotations

import logging
import click

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
    """Orchestrates multiple thing/project setup actions"""

    HANDLERS = {
        "database": CreateThingInPostgresHandler,
        "minio": CreateThingInMinioHandler,
        "mqtt": CreateMqttUserHandler,
        "grafana": CreateThingInGrafanaHandler,
        "frost": CreateFrostInstanceHandler,
        "crontab": CreateThingInCrontabHandler,
    }

    def __init__(self, actions: list[str]):
        """
        Args:
            actions: List of action names to execute (in order)
        """
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        self.handlers = self._initialize_handlers(actions)

    def _initialize_handlers(
        self, actions: list[str]
    ) -> list[tuple[str, AbstractHandler]]:
        """Create handler instances for requested actions"""
        handlers = []
        invalid_actions = [a for a in actions if a not in self.HANDLERS]

        if invalid_actions:
            available = ", ".join(self.HANDLERS.keys())
            raise ValueError(
                f"Unknown action(s): {', '.join(invalid_actions)}. "
                f"Available: {available}"
            )

        for action in actions:
            handler = self.HANDLERS[action]()
            handlers.append((action, handler))
            logger.info(f"Registered: {action}")

        return handlers

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        """Process all configured actions in sequence"""
        thing_uuid = content.get("thing")
        total = len(self.handlers)
        logger.info(
            f"Processing thing {thing_uuid} ({total} action{'s' if total > 1 else ''})"
        )

        success, failed = [], []

        for action_name, handler in self.handlers:
            try:
                handler.act(content, message)
                logger.info(f"✓ {action_name}")
                success.append(action_name)

            except Exception as e:
                logger.error(f"✗ {action_name}: {e}", exc_info=True)
                failed.append(action_name)

        # Summary
        if failed:
            logger.warning(
                f"Thing {thing_uuid}: {len(success)}/{total} succeeded, "
                f"{len(failed)} failed: {', '.join(failed)}"
            )
        else:
            logger.info(
                f"Thing {thing_uuid}: All {total} actions completed successfully"
            )


@click.command()
@click.argument(
    "actions",
    nargs=-1,
    type=click.Choice(
        list(SetupThingHandler.HANDLERS.keys()) + ["all"], case_sensitive=False
    ),
)
def main(actions: tuple[str, ...]):
    """Setup handler for IoT things - orchestrates infrastructure provisioning.

    \b
    Available actions:
      database  - PostgreSQL user/schema/tables
      minio     - MinIO bucket/policy
      mqtt      - MQTT user credentials
      grafana   - Grafana dashboard and organization
      frost     - FROST-Server instance
      crontab   - Scheduled job entry

    \b
    Examples:
      setup_thing.py                      # Run all actions
      setup_thing.py all                  # Run all actions
      setup_thing.py database minio       # Specific actions only
    """
    # Resolve "all" or empty to full list
    if not actions or "all" in actions:
        actions = list(SetupThingHandler.HANDLERS.keys())

    logger.info(f"Starting with actions: {', '.join(actions)}")

    handler = SetupThingHandler(list(actions))
    handler.run_loop()


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    main()
