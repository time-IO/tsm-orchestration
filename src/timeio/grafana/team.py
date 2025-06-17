from __future__ import annotations

from typing import TYPE_CHECKING

from timeio.grafana.typehints import TeamT
from timeio.grafana.utils import get_dict_by_key_value, logger

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaTeam:
    def __init__(self, api: TimeioGrafanaApi) -> None:
        self.api = api

    def get_by_name(self, name: str) -> TeamT | None:
        teams = self.api.teams.search_teams()
        return get_dict_by_key_value(teams, "name", name)

    def create(self, name, org_id) -> TeamT:
        res = self.api.teams.add_team({"name": name, "orgId": org_id})
        logger.debug(f"Created new team '{name}'")
        return self.get_by_name(name)
