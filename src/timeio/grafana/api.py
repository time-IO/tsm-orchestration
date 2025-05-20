from __future__ import annotations

from grafana_client import GrafanaApi
import logging
from types import SimpleNamespace
from timeio.grafana.organization import GrafanaOrganization
from timeio.grafana.team import GrafanaTeam
from timeio.grafana.folder import GrafanaFolder
from timeio.grafana.datasource import GrafanaDatasource
from timeio.grafana.dashboard import GrafanaDashboard


class TimeioGrafanaApi(GrafanaApi):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logger = logging.getLogger("timeio-grafana-api")
        self.timeio = SimpleNamespace(
            organization=GrafanaOrganization(api=self, logger=logger),
            team=GrafanaTeam(api=self, logger=logger),
            folder=GrafanaFolder(api=self, logger=logger),
            datasource=GrafanaDatasource(api=self, logger=logger),
            dashboard=GrafanaDashboard(api=self, logger=logger),
        )

    @classmethod
    def connect_from_url(
        cls, url: str, credential: tuple[str, str]
    ) -> TimeioGrafanaApi:
        return super().from_url(url=url, credential=credential)
