from __future__ import annotations

import logging
import re
import time
from typing import Literal

import grafana_client.api
from grafana_client.client import GrafanaException

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.common import get_envvar, setup_logging

logger = logging.getLogger("grafana-user-setup")


class Grafana:

    def __init__(self, url: str, user: str, password: str):
        self.api = grafana_client.api.GrafanaApi.from_url(
            url=url, credential=(user, password)
        )

    def get_user_id(self, name, max_tries=5, sleep=2) -> int | None:
        for cnt in range(max_tries):
            try:
                return self.api.users.find_user(name).get("id")
            except GrafanaException:
                if cnt < max_tries - 1:
                    logger.debug(f"Fetching user {name!r} faild. Retrying...")
                time.sleep(sleep)
        return None

    def get_all_orgs(self) -> dict[str, int]:
        orgs = self.api.organizations.list_organization()
        return {org.get("name"): org.get("id") for org in orgs}

    def get_user_orgs(self, user_id) -> dict[str, str]:
        orgs = self.api.users.get_user_organisations(user_id)
        return {org.get("name"): org.get("role") for org in orgs}

    def update_user_orgs(self, user_id, user_name, new_orgs) -> None:
        old_orgs = self.get_user_orgs(user_id)
        user_add_orgs = new_orgs.keys() - old_orgs.keys()
        user_update_orgs = old_orgs.keys() & new_orgs.keys()
        user_delete_orgs = old_orgs.keys() - new_orgs.keys() - {"Main Org."}

        # todo: should we also really create new orgs that
        #  was never seen before? then we must also iterate
        #  over create_org_names outside this loop.

        # no, we don't want to create org names that don't yet exist in grafana
        # creating the orgs should be done by the grafana_dashboard_setup.py

        all_orgs = self.get_all_orgs()
        all_orgs.pop("Main Org.", None)
        # We iterate over all orgs in Grafana and add/update/delete user in respective org
        for org, org_id in all_orgs.items():
            self.api.organizations.switch_organization(org_id)
            new_role = new_orgs.get(org)
            old_role = old_orgs.get(org)
            if org in user_add_orgs:
                logger.debug(f"Add user to org. U=%s, O=%s", user_name, org)
                self.add_user_to_org(new_role, user_name)
                self.api.organizations.switch_organization(1)
                self.add_user_to_team(org, user_id)
            elif org in user_update_orgs:
                if new_role != old_role:
                    logger.debug(
                        f"Update user. U=%s, O=%s, R=%s", user_name, org, new_role
                    )
                    # grafana: "cannot change role for externally synced user"
                    # so we have to delete and re-add the user
                    self.remove_user_from_org(org)
                    self.add_user_to_org(new_role, user_name)
                self.api.organizations.switch_organization(1)
                if not self.user_in_team(org_id, user_id):
                    self.add_user_to_team(org, user_id)
            elif org in user_delete_orgs:
                logger.debug(f"Remove user from org. U=%s, O=%s", user_name, org)
                self.remove_user_from_org(org)
                self.api.organizations.switch_organization(1)
                self.remove_user_from_team(org, user_id)

    def add_user_to_org(self, role, login_name) -> None:
        user = {"role": role, "loginOrEmail": login_name}
        self.api.organization.add_user_current_organization(user)

    def remove_user_from_org(self, user_id) -> None:
        self.api.organization.delete_user_current_organization(user_id)

    def user_in_team(self, team_id, user_id) -> bool:
        team_members = self.api.teams.get_team_members(team_id)
        for member in team_members:
            if member.get("userId") == user_id:
                return True
        return False

    def get_team_id_by_name(self, org) -> int | None:
        team = self.api.teams.search_teams(query=org)
        if team:
            return self.api.teams.search_teams(query=org)[0].get("id")
        return None

    def add_user_to_team(self, org, user_id) -> None:
        team_id = self.get_team_id_by_name(org)
        if team_id and not self.user_in_team(team_id, user_id):
            self.api.teams.add_team_member(team_id, user_id)

    def remove_user_from_team(self, org, user_id) -> None:
        team_id = self.get_team_id_by_name(org)[0].get("id")
        if team_id and self.user_in_team(team_id, user_id):
            self.api.teams.remove_team_member(team_id, user_id)


class CreateGrafanaUserHandler(AbstractHandler):

    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        self.gf = Grafana(
            url=get_envvar("GRAFANA_URL"),
            user=get_envvar("GRAFANA_USER"),
            password=get_envvar("GRAFANA_PASSWORD"),
        )
        self.vo_group_key = get_envvar("VO_GROUP_KEY", "eduperson_entitlement")
        self.vo_login_key = get_envvar("VO_LOGIN_KEY", "eduperson_principal_name")
        # if true, vo group admins become grafana organization admins,
        # otherwise, they become editors
        self.gf_roles_from_vo_roles = get_envvar(
            "GF_ROLE_FROM_VO_ROLE", False, cast_to=bool
        )
        self.vo_admin_subgroup = get_envvar("VO_ADMIN_SUBGROUP", "ufz-sms-admin")
        self.allowed_vos = get_envvar("ALLOWED_VOS")

    def act(self, content: dict, message: MQTTMessage):
        user_name = content.get(self.vo_login_key)
        vo_groups = content.get(self.vo_group_key)
        if user_id := self.gf.get_user_id(user_name):
            logger.debug(f"Found user {user_name} with user_id {user_id}")
            gf_groups = self.map_vo_groups_to_gf_orgs(vo_groups)
            self.gf.update_user_orgs(user_id, user_name, gf_groups)
        else:
            logger.warning(f"Could not find user {user_name}. Skipping user sync.")

    def map_vo_groups_to_gf_orgs(
        self, vo_groups
    ) -> dict[str, Literal["Admin", "Editor"]]:
        """Translate VO groups to grafana groups."""
        orgs = {}
        allowed_vos = "|".join(self.allowed_vos.split(","))

        # match.group(1): the VO  (e.g. UFZ-Timeseries-Management) or None
        # match.group(2): the VO group  (e.g. DemoGroup)
        # match.group(3): VO_ADMIN_SUBGROUP with colon (e.g. :ufz-sms-admin) or None if not present
        # match.group(4): VO_ADMIN_SUBGROUP without colon (e.g. ufz-sms-admin) or None if not present
        pattern = rf"({allowed_vos}):([^:#]+)(:({self.vo_admin_subgroup or ''}))?"

        for vo_group in vo_groups:
            admin = org_name = role = None
            if match := re.search(pattern, vo_group):
                org_name = f"{match.group(1)}:{match.group(2)}"
                admin = match.group(4)
                role: Literal["Admin", "Editor"] = "Editor"
                if admin and self.gf_roles_from_vo_roles:
                    role = "Admin"
                orgs[org_name] = role

            logger.debug(
                "vo_group: %s\nvo_admin_subgroup: %s\ngf_org: %s\ngf_role: %s\n",
                *(vo_group, admin, org_name, role),
            )
        return orgs


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateGrafanaUserHandler().run_loop()
