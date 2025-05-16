from __future__ import annotations

from grafana_client import GrafanaApi
import logging
from timeio.grafana.organization import GrafanaOrganization
from timeio.grafana.team import GrafanaTeam
from timeio.grafana.folder import GrafanaFolder
from timeio.grafana.datasource import GrafanaDatasource

class TimeioGrafanaApi(GrafanaApi):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("timeio-grafana-api")
        self.organization_custom = GrafanaOrganization(api=self, logger=self.logger)
        self.team_custom = GrafanaTeam(api=self, logger=self.logger)
        self.folder_custom = GrafanaFolder(api=self, logger=self.logger)
        self.datasource_custom = GrafanaDatasource(api=self, logger=self.logger)
    @classmethod
    def connect_from_url(cls, url: str, credential: tuple[str, str]) -> TimeioGrafanaApi:
        return super().from_url(url=url, credential=credential)
