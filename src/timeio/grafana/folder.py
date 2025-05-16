from __future__ import annotations

from typing import TYPE_CHECKING
from logging import Logger

from timeio.grafana.typed_dicts import FolderT
from timeio.grafana.utils import value_from_dict_list, _exists

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi

class GrafanaFolder:
    def __init__(self, api: TimeioGrafanaApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def exists(self, uuid) -> bool:
        return _exists(self.api.folder.get_folder, uuid)

    def get_by_uid(self, uid: str) -> FolderT | None:
        folders = self.api.folder.get_all_folders()
        return value_from_dict_list(folders, "uid", uid)

    def get_by_name(self, name: str) -> FolderT | None:
        folders = self.api.folder.get_all_folders()
        return value_from_dict_list(folders, "name", name)

    def create(self, name: str, uid: str) -> FolderT:
        folder = self.api.folder.create_folder(title=name, uid=uid)
        self.logger.debug(f"Created new folder '{name}'")

    def set_permissions(self, folder, team, role):
        if role == 1:
            # set GRAFANA_USER as folder admin and team as Viewer
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"teamId": team["id"], "permission": 1},
                ]
            }
        else:
            # allow role Editor to edit folder
            permissions = {
                "items": [
                    {"userId": 1, "permission": 4},
                    {"role": "Admin", "permission": 4},
                    {"role": "Editor", "permission": role},
                ]
            }
        self.api.folder.update_folder_permissions(folder["uid"], permissions)
        self.logger.debug(f"Set permissions on folder '{folder['name']}' for role '{role}'")
