from __future__ import annotations

from typing import TYPE_CHECKING
from logging import Logger

from timeio.grafana.typing import OrgT
from timeio.grafana.utils import get_dict_by_key_value

if TYPE_CHECKING:
    from timeio.grafana.api import TimeioGrafanaApi


class GrafanaOrganization:
    def __init__(self, api: TimeioGrafanaApi, logger: Logger) -> None:
        self.api = api
        self.logger = logger

    def get_organization_by_id(self, org_id: int) -> OrgT | None:
        organizations = self.api.organizations.list_organization()
        return get_dict_by_key_value(organizations, "id", org_id)

    def get_organization_by_name(self, name: str) -> OrgT | None:
        organizations = self.api.organizations.list_organization()
        return get_dict_by_key_value(organizations, "name", name)

    def create_organization(self, name: str) -> OrgT:
        org = self.api.organization.create_organization({"name": name})
        self.logger.debug(f"Created new organization '{name}'")
        return self.get_organization_by_name(name)
