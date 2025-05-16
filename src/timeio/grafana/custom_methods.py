from __future__ import annotations

from logging import Logger
from urllib.parse import urlparse
from typing import List, Dict, Any, TYPE_CHECKING
from grafana_client.client import GrafanaException

from timeio.grafana.typed_dicts import TeamT, OrgT, FolderT, DatasourceT
from timeio.crypto import decrypt, get_crypt_key
from timeio.thing import Thing

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi

class CustomGrafanaMethods:
    def __init__(self, api: TimeioGrafanaApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    # This method is used to find a dictionary in a list of dictionaries
    @staticmethod
    def value_from_dict_list(dict_list: List[Dict], key: str, value: Any):
        for d in dict_list:
            if d.get(key) == value:
                return d
        return None

    # This method is used to check if a resource exists in Grafana
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

    # Datasource
    def get_datasource_by_name(self, name: str) -> DatasourceT | None:
        datasources = self.api.datasource.list_datasources()
        return self.value_from_dict_list(datasources, "name", name)

    def get_datasource_by_uid(self, uid: str) -> DatasourceT | None:
        datasources = self.api.datasource.list_datasources()
        return self.value_from_dict_list(datasources, "uid", uid)

    def create_datasource(self, thing: Thing, user_prefix: str, sslmode: str) -> DatasourceT:
        db_user = user_prefix + thing.database.ro_username
        db_pass = decrypt(thing.database.ro_password, get_crypt_key())
        db_url_parsed = urlparse(thing.database.url)
        db_path = db_url_parsed.path.lstrip("/")
        db_url = db_url_parsed.hostname
        if db_url_parsed.port is not None:  # only add port, if it is defined
            db_url += f":{db_url_parsed.port}"
        datasource = {
            "name": thing.project.name,
            "uid": thing.project.uuid,
            "type": "postgres",
            "url": db_url,
            "user": db_user
            "access": "proxy",
            "basicAuth": False,
            "jsonData": {
                "database": db_path,
                "sslmode": sslmode,
                "timescaledb": False,
            },
            "secureJsonData": {"password": db_pass},
        }
        self.api.datasource.create_datasource(datasource)
        self.logger.debug(f"Created new datasource '{datasource['name']}'")
        return self.get_datasource_by_name(thing.project.name)