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
    """Orchestrates multiple thing/project setup actions"""

    HANDLERS = {
        "database": CreateThingInPostgresHandler,
        "minio": CreateThingInMinioHandler,
        "mqtt": CreateMqttUserHandler,
        "grafana": CreateThingInGrafanaHandler,
        "frost": CreateFrostInstanceHandler,
        "crontab": CreateThingInCrontabHandler,
    }

    def __init__(self, actions: list[str], fail_fast: bool = False):
        """
        Args:
            actions: List of action names to execute (in order)
            fail_fast: If True, stop on first error; if False, continue with remaining actions
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
        self.fail_fast = fail_fast
        self.handlers = self._initialize_handlers(actions)
        
    def _initialize_handlers(self, actions: list[str]) -> list[tuple[str, AbstractHandler]]:
        """Create handler instances for requested actions"""
        handlers = []
        
        for action in actions:
            if action not in self.HANDLERS:
                raise ValueError(
                    f"Unknown action: {action}. "
                    f"Available: {', '.join(self.HANDLERS.keys())}"
                )
            
            handler_class = self.HANDLERS[action]
            handler = handler_class()
            handlers.append((action, handler))
            logger.info(f"Registered action: {action}")
        return handlers

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        """Process all configured actions in sequence"""
        thing_uuid = content.get("thing")
        logger.info(f"Processing thing {thing_uuid} with {len(self.handlers)} actions")

        results = {"success": [], "failed": []}

        for action_name, handler in self.handlers:
            logger.info(f"Executing action: {action_name}")
            
            try:
                handler.act(content, message)
                logger.info(f"✓ Completed: {action_name}")
                results["success"].append(action_name)
            
            except Exception as e:
                logger.error(f"✗ Failed: {action_name} - {e}", exc_info=True)
                results["failed"].append(action_name)

                if self.fail_fast:
                    logger.error("Stopping due to error(fail_fast=True)")
                    raise

        # Summary
        logger.info(
            f"Thing {thing_uuid} setup complete: "
            f"{len(results['success'])} succeeded, {len(results['failed'])} failed"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Combined thing setup handler - orchestrates thing setup actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available actions:
  database   - PostgreSQL user/schema/tables
  minio      - MinIO user/bucket/policy
  mqtt       - MQTT user credentials
  grafana    - Grafana dashboard and organization
  frost      - FROST-Server instance
  crontab    - Crontab entry for scheduled jobs

Examples:
  python setup_thing.py                    # Run all actions
  python setup_thing.py all                # Run all actions
  python setup_thing.py database minio     # Only database and storage
  python setup_thing.py --fail-fast all    # Stop on first error
""",
    )

    parser.add_argument(
        "actions",
        nargs="*",
        choices=list(SetupThingHandler.HANDLERS.keys()) + ["all"],
        help="Setup actions to perform (in order, default: all)",
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on first error (default: continue with remaining actions)",
    )

    args = parser.parse_args()

    # Resolve "all" to actual action list
    actions = (
        list(SetupThingHandler.HANDLERS.keys())
        if not args.actions or args.actions == ["all"]
        else args.actions
    )

    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    logger.info(f"Starting combined thing setup handler with actions: {', '.join(actions)}")

    handler = SetupThingHandler(actions, fail_fast=args.fail_fast)
    handler.run_loop()


if __name__ == "__main__":
    main()
