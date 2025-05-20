from __future__ import annotations

from typing import TYPE_CHECKING

from timeio.grafana.utils import _exists, logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaUser:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def exists(self, name: str) -> bool:
        return _exists(self.api.users.find_user, name)
