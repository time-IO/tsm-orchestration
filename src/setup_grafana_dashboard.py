import logging
from urllib.parse import urlparse

from grafana_client import GrafanaApi
from grafana_client.client import GrafanaException

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.crypto import decrypt, get_crypt_key
from timeio.typehints import MqttPayload

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
        self.create_organization(thing)

        # create datasource, folder, dashboard in project org
        # Give Grafana and Org Admins admin access to folder
        # Give Role Editor edit access to folder
        org_id = self.organization_from_list(thing.project.name).get("id")
        self.create_all_in_org(thing, org_id=org_id, role=2)

        # create team, datasource, folder, dashboard in Main org
        # Give Team viewer access to folder
        self.create_all_in_org(thing, org_id=1, role=1)

    def create_all_in_org(self, thing, org_id, role):
        self.api.organizations.switch_organization(org_id)
        self.create_datasource(thing, user_prefix="grf_")
        self.create_folder(thing)
        # only create team in Main org
        if org_id == 1:
            self.create_team(thing, org_id)
        self.set_folder_permissions(thing, role)
        self.create_dashboard(thing)

    def create_organization(self, thing):
        name = thing.project.name
        if not self.organization_exists(name):
            self.api.organization.create_organization({"name": name})
            logger.debug(f"Created organization {name}")
        else:
            logger.debug(f"Organization {name} already exists")

    def create_team(self, thing, org_id):
        name = thing.project.name
        if not self.team_exists(name):
            self.api.teams.add_team({"name": name, "orgId": org_id})
            logger.debug(f"Created team {name}")
        else:
            logger.debug(f"Team {name} already exists")

    def create_folder(self, thing):
        uid = thing.project.uuid
        name = thing.project.name
        if not self.folder_exists(uid):
            self.api.folder.create_folder(name, uid)
            logger.debug(f"Created folder {name}")
        else:
            logger.debug(f"Folder {name} already exists")

    def create_datasource(self, thing, user_prefix: str):
        uuid, name = thing.project.uuid, thing.project.name
        if not self.datasource_exists(uuid):
            datasource = self.new_datasource(thing, user_prefix)
            self.api.datasource.create_datasource(datasource)
            logger.debug(f"Created datasource {name}")
        else:
            logger.debug(f"Datasource {name} already exists")

    def create_dashboard(self, thing, overwrite=True):
        # create/update dashboard if it doesn't exist or overwrite is True
        if overwrite or not self.dashboard_exists(thing.uuid):
            dashboard = self.build_dashboard_dict(thing)
            self.api.dashboard.update_dashboard(dashboard)
            action = "Updated" if overwrite else "Created"
            logger.debug(f"{action} dashboard {thing.name}")
        else:
            logger.debug(f"Dashboard {thing.name} already exists")

    def new_datasource(self, thing, user_prefix: str):
        ds_uid = thing.project.uuid
        ds_name = thing.project.name
        db_user = user_prefix.lower() + thing.database.ro_username.lower()
        db_password = decrypt(thing.database.ro_password, get_crypt_key())

        # parse thing.database.url to get hostname, port, database name
        db_url_parsed = urlparse(thing.database.url)
        db_path = db_url_parsed.path.lstrip("/")
        # only add port, if it is defined
        db_url = db_url_parsed.hostname
        if db_url_parsed.port is not None:
            db_url += f":{db_url_parsed.port}"

        return {
            "name": ds_name,
            "uid": ds_uid,
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

    def organization_from_list(self, name):
        organizations = self.api.organizations.list_organization()
        for org in organizations:
            if org.get("name") == name:
                return org
        return None

    def _exists(self, func: callable, *args) -> bool:
        try:
            func(*args)
        except GrafanaException:
            return False
        else:
            return True

    def organization_exists(self, name) -> bool:
        return self.organization_from_list(name) is not None

    def datasource_exists(self, uuid) -> bool:
        return self._exists(self.api.datasource.get_datasource_by_uid, uuid)

    def dashboard_exists(self, uuid) -> bool:
        return self._exists(self.api.dashboard.get_dashboard, uuid)

    def folder_exists(self, uuid) -> bool:
        return self._exists(self.api.folder.get_folder, uuid)

    def team_exists(self, name) -> bool:
        return bool(self.api.teams.search_teams(query=name))

    def set_folder_permissions(self, thing, role):
        name, uuid = thing.project.name, thing.project.uuid
        current_org = self.api.organization.get_current_organization()
        if role == 1:
            team_id = self.api.teams.search_teams(query=name)[0].get("id")
            # set GRAFANA_USER as folder admin and team as Viewer
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"teamId": team_id, "permission": role},
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
        self.api.folder.update_folder_permissions(uuid, permissions)

    def build_dashboard_dict(self, thing):
        dashboard_uid = thing.uuid
        dashboard_title = thing.name
        folder_uid = thing.project.uuid
        folder_title = thing.project.name
        datasource_dict = {"type": "postgres", "uid": folder_uid}

        # template variable for datastream positions/properties
        datastream_sql = f"""
            SELECT property FROM datastream_properties 
            WHERE t_uuid::text = '{thing.uuid}'
        """
        datastream_templating = {
            "datasource": datasource_dict,
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
            "datasource": datasource_dict,
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
            "datasource": datasource_dict,
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
                    "datasource": datasource_dict,
                    "editorMode": "code",
                    "format": "time_series",
                    "rawQuery": True,
                    "rawSql": observation_sql,
                    "refId": "A",
                },
                {
                    "datasource": datasource_dict,
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
                    "panels": [self._journal_table(thing, datasource_dict)],
                    "title": "Status Journal New 0",
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
            "tags": [folder_title, dashboard_title, "TSM_automation"],
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
            "folderUid": folder_uid,
            "message": "created by TSM dashboard automation",
            "overwrite": True,
        }

    def _journal_table(self, thing: Thing, datasource: dict[str, str]):

        return {
            "datasource": datasource,
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {
                            "options": {
                                "ERROR": {"color": "#9d545d", "index": 2},
                                "INFO": {"color": "#6d9967", "index": 0},
                                "WARNING": {"color": "#b48250", "index": 1},
                            },
                            "type": "value",
                        }
                    ]
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
            "gridPos": {"h": 12, "w": 24},
            "title": "Status Journal",
            "type": "table",
            "targets": [
                {
                    "datasource": datasource,
                    "refId": "A",
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": f"SELECT timestamp, level, message, origin "
                    f"FROM journal "
                    f"JOIN thing t on journal.thing_id = t.id "
                    f"WHERE t.uuid::text = '{thing.uuid}' "
                    f"ORDER BY timestamp DESC ",
                }
            ],
        }


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInGrafanaHandler().run_loop()
