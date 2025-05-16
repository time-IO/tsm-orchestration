from __future__ import annotations

from typing import TYPE_CHECKING
from logging import Logger

from timeio.grafana.typed_dicts import TeamT
from timeio.grafana.utils import value_from_dict_list

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi

class GrafanaTeam:
    def __init__(self, api: TimeioGrafanaApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def get_by_name(self, name: str) -> TeamT | None:
        teams = self.api.teams.search_teams()
        return value_from_dict_list(teams, "name", name)

    def create_team(self, name, org_id) -> TeamT:
        res = self.api.teams.add_team({"name": name, "orgId": org_id})
        self.logger.debug(f"Created new team '{name}'")
        return self.get_team_by_name(name)
