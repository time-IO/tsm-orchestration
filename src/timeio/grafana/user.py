from __future__ import annotations

from typing import TYPE_CHECKING
from logging import Logger

from timeio.grafana.typing import UserT
from timeio.grafana.utils import _exists

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaUser:
    def __init__(self, api: TimeioGrafanaApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def exists(self, name: str) -> bool:
        return _exists(self.api.users.find_user, name)
