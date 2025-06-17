from __future__ import annotations

from grafana_client import GrafanaApi
from types import SimpleNamespace

from timeio.grafana.organization import GrafanaOrganization
from timeio.grafana.team import GrafanaTeam
from timeio.grafana.folder import GrafanaFolder
from timeio.grafana.datasource import GrafanaDatasource
from timeio.grafana.dashboard import GrafanaDashboard
from timeio.grafana.utils import logger


class TimeioGrafanaApi(GrafanaApi):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timeio = SimpleNamespace()
        self.timeio.organization = GrafanaOrganization(self)
        self.timeio.team = GrafanaTeam(self)
        self.timeio.folder = GrafanaFolder(self)
        self.timeio.datasource = GrafanaDatasource(self)
        self.timeio.dashboard = GrafanaDashboard(self)

    @classmethod
    def connect_from_url(cls, url: str, credential: tuple[str, str]) -> TimeioGrafanaApi:
        return super().from_url(url=url, credential=credential)
