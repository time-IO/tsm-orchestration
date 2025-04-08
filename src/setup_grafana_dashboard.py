from __future__ import annotations

import logging
from urllib.parse import urlparse

from grafana_client import GrafanaApi
from grafana_client.client import GrafanaException

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload
from typing import TypedDict, Any

logger = logging.getLogger("grafana-dashboard-setup")

TeamT = TypedDict("TeamT", {"id": int, "uid": str, "title": str})
OrgT = TypedDict("OrgT", {"id": int, "name": str, "address": dict[str, str]})
FolderT = TypedDict(
    "FolderT",
    {
        "id": int,
        "uid": str,
        "orgId": int,
        "title": str,
        "url": str,
        "hasAcl": bool,
        "canSave": bool,
        "canEdit": bool,
        "canAdmin": bool,
        "canDelete": bool,
        "createdBy": str,
        "created": str,
        "updatedBy": str,
        "updated": str,
        "version": int,
    },
)

DatasourceT = TypedDict(
    "DatasourceT",
    {
        "id": int,
        "uid": str,
        "orgId": int,
        "name": str,
        "type": str,
        "typeName": str,
        "typeLogoUrl": str,
        "access": str,
        "url": str,
        "user": str,
        "database": str,
        "basicAuth": bool,
        "isDefault": bool,
        "jsonData": dict[str, Any],
        "readOnly": bool,
    },
)


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

        self.api = GrafanaApi.from_url(
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

        self.set_folder_permissions(folder, team_name, role)

        action = "Updated" if self.dashboard_exists(thing.uuid) else "Created new"
        dashboard = self.build_dashboard(thing, folder, ds)
        self.api.dashboard.update_dashboard(dashboard)
        logger.debug(f"{action} dashboard {thing.name}")

    def get_organization(self, name) -> OrgT | None:
        organizations = self.api.organizations.list_organization()
        for org in organizations:
            if org.get("name") == name:
                return org
        return None

    def create_organization(self, name) -> OrgT:
        self.api.organization.create_organization({"name": name})
        logger.debug(f"Created new organization {name}")
        return self.api.organization.find_organization(name)

    def get_team(self, thing) -> TeamT | None:
        """Return team and maybe create it."""
        name = thing.project.name
        if teams := self.api.teams.search_teams(query=name):
            logger.debug(f"Team {name} already exists")
            return teams[0]
        return None

    def create_team(self, thing, org_id) -> TeamT:
        """Return team and maybe create it."""
        name = thing.project.name
        res = self.api.teams.add_team({"name": name, "orgId": org_id})
        logger.debug(f"Created new team {name}")
        return self.api.teams.get_team(res["teamId"])

    def get_folder(self, thing) -> FolderT | None:
        uid = thing.project.uuid
        if self.folder_exists(uid):
            return self.api.folder.get_folder(uid)
        return None

    def create_folder(self, thing) -> FolderT:
        uid = thing.project.uuid
        name = thing.project.name
        self.api.folder.create_folder(name, uid)
        logger.debug(f"Created new folder {name}")
        return self.api.folder.get_folder(uid)

    def set_folder_permissions(self, folder, team, role):
        if role == 1:
            # set GRAFANA_USER as folder admin and team as Viewer
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"teamId": team["id"], "permission": role},
                ]
            }
        else:
            logger.debug(f"Set folder permissions for role {role}")
            # allow role Editor to edit folder
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"role": "Admin", "permission": 4},
                    {"role": "Editor", "permission": role},
                ]
            }
        self.api.folder.update_folder_permissions(folder["uid"], permissions)

    def get_datasource(self, thing) -> DatasourceT | None:
        uid = thing.project.uuid
        if self.datasource_exists(uid):
            return self.api.datasource.get_datasource_by_uid(uid)
        return None

    def create_datasource(self, thing, user_prefix: str):
        name = thing.project.name
        uid = thing.project.uuid
        db_user = user_prefix.lower() + thing.database.ro_username.lower()
        db_password = decrypt(thing.database.ro_password, get_crypt_key())

        db_url_parsed = urlparse(thing.database.url)
        db_path = db_url_parsed.path.lstrip("/")
        db_url = db_url_parsed.hostname
        if db_url_parsed.port is not None:  # only add port, if it is defined
            db_url += f":{db_url_parsed.port}"
        self.api.datasource.create_datasource(
            {
                "name": name,
                "uid": uid,
                "type": "postgres",
                "url": db_url,
                "user": db_user,
                "access": "proxy",
                "basicAuth": False,
                "jsonData": {
                    "database": db_path,
                    "sslmode": self.sslmode,
                    "timescaledb": True,
                },
                "secureJsonData": {"password": db_password},
            }
        )
        logger.debug(f"Created new datasource {name}")
        return self.api.datasource.get_datasource_by_uid(uid)

    def _exists(self, func: callable, *args) -> bool:
        try:
            func(*args)
        except GrafanaException:
            return False
        else:
            return True

    def datasource_exists(self, uuid) -> bool:
        return self._exists(self.api.datasource.get_datasource_by_uid, uuid)

    def dashboard_exists(self, uuid) -> bool:
        return self._exists(self.api.dashboard.get_dashboard, uuid)

    def folder_exists(self, uuid) -> bool:
        return self._exists(self.api.folder.get_folder, uuid)

    def build_dashboard(self, thing, folder: FolderT, datasource: DatasourceT):
        dashboard_uid = thing.uuid
        dashboard_title = thing.name
        # datasource = {"type": datasource["type"], "uid": datasource["uid"]}

        # template variable for datastream positions/properties
        datastream_sql = f"""
            SELECT property FROM datastream_properties 
            WHERE t_uuid::text = '{thing.uuid}'
        """
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
        observation_sql = f"""
            WITH date_filtered AS (
            -- This query returns the data chosen by the datepicker, or
            -- returns null if no data is in the selected date range.
              SELECT
                o.result_time AS "time",
                o.result_number AS "value"
              FROM observation o
              WHERE $__timeFilter(o.result_time)
              AND o.datastream_id = (
                  SELECT dp.ds_id FROM datastream_properties dp
                  WHERE ${{datastream_pos:singlequote}} in (dp.property, dp.position)
                  AND dp.t_uuid :: text = '{thing.uuid}')
              ORDER BY o.result_time DESC
              LIMIT 1000000  -- 1M
            ),
            fallback AS (
            -- This query returns the most recent 10k datapoints
              SELECT
                o.result_time AS "time",
                o.result_number AS "value"
              FROM observation o
              WHERE o.datastream_id = (
                SELECT dp.ds_id FROM datastream_properties dp
                WHERE ${{datastream_pos:singlequote}} in (dp.property, dp.position)
                AND dp.t_uuid :: text = '{thing.uuid}')
              ORDER BY o.result_time DESC  -- most recent
              LIMIT 10000  -- 10k
            )
            -- First the date_filtered query is executed. If it returns
            -- null, because the user selected a time range without any
            -- data, the fallback query is executed and return the most
            -- recent 10k data points. This fallback data is not shown
            -- immediately, because it is also not the selected timerange,
            -- but grafana will now show a ZoomToData button. If the user
            -- press the button, the panel will jump to the data from the
            -- fallback query (the most recent 10k data points).
            SELECT * FROM date_filtered
            UNION ALL
            SELECT * FROM fallback
            WHERE NOT EXISTS (SELECT 1 FROM date_filtered)
            ORDER BY "time" ASC
        """

        qaqc_sql = f"""
            -- Using "result_quality -> -1 ->>" because result_quality is an array of quality objects 
            -- we use "-1" to always select the last one              
            SELECT o.result_time AS "time",
            1 AS "quality_flag",
            jsonb_build_object(
                'annotation', CAST ((result_quality -> -1 ->> 'annotation') AS DECIMAL),
                'measure', result_quality -> -1 ->> 'properties', 'measure',
                'user_label', result_quality -> -1 ->> 'properties', 'userLabel'
            ) AS "qaqc_result"
            FROM observation o
            WHERE o.datastream_id = (
                SELECT dp.ds_id
                FROM datastream_properties dp
                WHERE ${{datastream_pos:singlequote}} in (dp.property,dp.position)
                AND dp.t_uuid::text = '{thing.uuid}'
            ) AND ${{show_qaqc_flags}} = 'True'
            AND result_quality IS NOT NULL
            AND result_quality <> 'null'
            AND (result_quality -> -1 ->> 'annotation') IS NOT NULL
            AND (result_quality -> -1 ->> 'annotation') <> '0.0'
            AND (result_quality -> -1 ->> 'annotation') <> '-inf'
            ORDER BY o.result_time ASC
        """
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
                    "rawSql": (
                        f"SELECT timestamp, level, message, origin "
                        f"FROM journal "
                        f"JOIN thing t on journal.thing_id = t.id "
                        f"WHERE t.uuid::text = '{thing.uuid}' "
                        f"ORDER BY timestamp DESC "
                    ),
                    "refId": "A",
                }
            ],
            "datasource": datasource,
        }


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInGrafanaHandler().run_loop()
