from __future__ import annotations

import logging
from urllib.parse import urlparse

from timeio.grafana.api import TimeioGrafanaApi


from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload
from typing import TypedDict, Any

logger = logging.getLogger("grafana-dashboard-setup")


class CreateThingInGrafanaHandler(AbstractHandler):
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

        self.api = TimeioGrafanaApi.from_url(
            url=get_envvar("GRAFANA_URL"),
            credential=(
                get_envvar("GRAFANA_USER"),
                get_envvar("GRAFANA_PASSWORD"),
            ),
        )
        # needed when defining new datasource
        self.sslmode = get_envvar("GRAFANA_DEFAULT_DATASOURCE_SSLMODE")
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        org = self.get_organization(thing.project.name)
        if org is None:
            org = self.create_organization(thing.project.name)

        # create datasource, folder, dashboard in project org
        # Give Grafana and Org Admins admin access to folder
        # Give Role Editor edit access to folder
        self.create_all_in_org(thing, org_id=org["id"], role=2)

        # create team, datasource, folder, dashboard in Main org
        # Give Team viewer access to folder
        self.create_all_in_org(thing, org_id=1, role=1)

    def create_all_in_org(self, thing, org_id, role):
        self.api.organizations.switch_organization(org_id)
        if (ds := self.get_datasource(thing)) is None:
            ds = self.create_datasource(thing, user_prefix="grf_")

        if (team_name := self.get_team(thing)) is None and org_id == 1:
            # only create team in Main org
            team_name = self.create_team(thing, org_id)

        if (folder := self.get_folder(thing)) is None:
            folder = self.create_folder(thing)

        self.api.folder_custom.set_permissions(folder, team_name, role)

        action = "Updated" if self.dashboard_exists(thing.uuid) else "Created new"
        dashboard = self.build_dashboard(thing, folder, ds)
        self.api.dashboard.update_dashboard(dashboard)
        logger.debug(f"{action} dashboard {thing.name}")

    def build_dashboard(self, thing, folder: FolderT, datasource: DatasourceT):
        dashboard_uid = thing.uuid
        dashboard_title = thing.name

        datastream_sql = ""  # get from sql/datastream.sql

        datastream_templating = {
            "datasource": datasource,
            "hide": 0,
            "includeAll": True,
            "label": "Datastream",
            "multi": True,
            "name": "datastream_pos",
            "query": datastream_sql,
            "refresh": 1,
            "sort": 7,
            "type": "query",
        }

        show_qaqc_templating = {
            "datasource": datasource,
            "hide": 0,
            "type": "custom",
            "name": "show_qaqc_flags",
            "label": "Show QAQC Flags",
            "query": "False,True",
            "multi": False,
            "includeAll": False,
            "options": [
                {"text": "False", "value": "False", "selected": True},
                {"text": "True", "value": "True", "selected": False},
            ],
        }

        # query to get observations, used in timeseries panel
        observation_sql = ""  # get from sql/observation.sql

        qaqc_sql = ""  # get from sql/qaqc.sql

        show_qaqc_overrides = {
            "matcher": {
                "id": "byFrameRefID",
                "options": "B",
            },
            "properties": [
                {"id": "custom.drawStyle", "value": "points"},
                {"id": "custom.axisPlacement", "value": "hidden"},
                {"id": "custom.axisSoftMax", "value": 1},
                {"id": "custom.pointSize", "value": 7},
            ],
        }
        # build observations panel dict
        observation_panel = {
            "datasource": datasource,
            "gridPos": {"h": 8},
            "options": {
                "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": False,
                }
            },
            "maxPerRow": 3,
            "repeat": "datastream_pos",
            "repeatDirection": "h",
            "fieldConfig": {
                "overrides": [show_qaqc_overrides],
            },
            "targets": [
                {
                    "datasource": datasource,
                    "editorMode": "code",
                    "format": "time_series",
                    "rawQuery": True,
                    "rawSql": observation_sql,
                    "refId": "A",
                },
                {
                    "datasource": datasource,
                    "editorMode": "code",
                    "format": "time_series",
                    "rawQuery": True,
                    "rawSql": qaqc_sql,
                    "refId": "B",
                },
            ],
            "title": "$datastream_pos",
            "type": "timeseries",
        }

        # build dashboard dictionary
        dashboard = {
            "editable": True,
            "liveNow": True,
            "panels": [
                {
                    "collapsed": True,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
                    "panels": [self._journal_table(thing, datasource)],
                    "title": "Status Journal",
                    "type": "row",
                },
                {
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24},
                    "panels": [],
                    "title": "Observations",
                    "type": "row",
                },
                observation_panel,
            ],
            "refresh": False,
            "tags": [folder["title"], dashboard_title, "TSM_automation"],
            "templating": {
                "list": [
                    datastream_templating,
                    show_qaqc_templating,
                ]
            },
            "time": {"from": "now-7d", "to": "now"},
            "title": dashboard_title,
            "uid": dashboard_uid,
        }

        # query to get journal messages
        return {
            "dashboard": dashboard,
            "folderUid": folder["uid"],
            "message": "created by TSM dashboard automation",
            "overwrite": True,
        }

    def _journal_table(self, thing: Thing, datasource: dict[str, str]):
        """Create the journal table"""

        return {
            "type": "table",
            "title": "Status Journal",
            "gridPos": {"h": 12, "w": 24},
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "filterable": True,
                    },
                    "mappings": [
                        {
                            "options": {
                                "ERROR": {"color": "#9d545d", "index": 2},
                                "INFO": {"color": "#6d9967", "index": 0},
                                "WARNING": {"color": "#b48250", "index": 1},
                            },
                            "type": "value",
                        }
                    ],
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "level"},
                        "properties": [
                            {
                                "id": "custom.cellOptions",
                                "value": {
                                    "applyToRow": True,
                                    "mode": "gradient",
                                    "type": "color-background",
                                },
                            }
                        ],
                    }
                ],
            },
            "transparent": True,
            "targets": [
                {
                    "datasource": datasource,
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": "",  # get from sql/journal.sql
                    "refId": "A",
                }
            ],
            "datasource": datasource,
        }


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInGrafanaHandler().run_loop()
