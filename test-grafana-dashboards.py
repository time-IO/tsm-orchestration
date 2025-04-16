#!/usr/bin/env python3

from __future__ import annotations
import sys
import os
import logging
from typing import Set, AnyStr

from dotenv import load_dotenv
from grafana_client import GrafanaApi
import psycopg
from psycopg import Connection


def main():
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
    load_dotenv()
    configdb_dsn = os.environ.get("CONFIGDB_READONLY_DSN")

    # !!! should be removed after testing locally
    configdb_dsn = configdb_dsn.replace("database", "localhost")
    # !!!

    grafana_url = os.environ.get("VISUALIZATION_PROXY_URL")
    grafana_user = os.environ.get("VISUALIZATION_USER")
    grafana_pass = os.environ.get("VISUALIZATION_PASSWORD")

    with psycopg.connect(configdb_dsn) as conn:
        things = get_configdb_things(conn)
        projects = get_configdb_projects(conn)

    api = GrafanaApi.from_url(url=grafana_url, credential=(grafana_user, grafana_pass))

    orgs = get_org_names(api)
    dashboards_main_org = get_dashboard_uuids_main_org(api)
    dashboards_other_orgs = get_dashboard_uuids_other_orgs(api)

    logging.debug(f"Projects: \n{projects}")
    logging.debug(f"Organizations: \n{orgs}")
    logging.debug(f"Things: \n{things}")
    logging.debug(f"Dashboards (Main Org.): \n{dashboards_main_org}")
    logging.debug(f"Dashboards (Project Orgs): \n{dashboards_other_orgs}")

    orgs_incomplete = check_missing_orgs(projects, orgs)
    dashboards_incomplete = check_missing_dashboards(
        things, dashboards_main_org, dashboards_other_orgs
    )

    if orgs_incomplete or dashboards_incomplete:
        sys.exit(1)


def get_configdb_things(conn: Connection) -> Set[AnyStr]:
    with conn.cursor() as cur:
        # Execute a query
        cur.execute("SELECT uuid::varchar from thing")
        return {row[0] for row in cur.fetchall()}


def get_configdb_projects(conn: Connection) -> Set[AnyStr]:
    with conn.cursor() as cur:
        # Execute a query
        cur.execute("SELECT name from project")
        return {row[0] for row in cur.fetchall()}


def get_org_names(api: GrafanaApi) -> Set[AnyStr]:
    orgs = api.organizations.list_organization()[1:]
    return {o.get("name") for o in orgs}


def get_org_ids(api: GrafanaApi) -> Set[int]:
    orgs = api.organizations.list_organization()[1:]
    return {o.get("id") for o in orgs}


def get_dashboard_uuids_main_org(api: GrafanaApi) -> Set[AnyStr]:
    api.organizations.switch_organization(1)
    dashboards = api.search.search_dashboards(type_="dash-db")
    return {d.get("uid") for d in dashboards}


def get_dashboard_uuids_other_orgs(api: GrafanaApi) -> Set[AnyStr]:
    orgs = get_org_ids(api)
    dashboards = set()
    for org in orgs:
        api.organizations.switch_organization(org)
        dashboard_dicts = api.search.search_dashboards(type_="dash-db")
        dashboards.update({d.get("uid") for d in dashboard_dicts})
    return dashboards


def check_missing_orgs(projects: Set[AnyStr], orgs: Set[AnyStr]) -> bool:
    """
    Check if there is a grafana org for each time.IO project
    """
    missing_orgs = projects - orgs
    if not missing_orgs:
        logging.info("No missing orgs")
        return False
    else:
        logging.error(f"Missing orgs: \n{missing_orgs}")
        return True


def check_missing_dashboards(
    things: Set[AnyStr],
    dashboards_main_org: Set[AnyStr],
    dashboards_other_orgs: Set[AnyStr],
) -> bool:
    """
    Check if there are dashboards for each time.IO thing in main org and respective project org
    """
    missing_main_org = things - dashboards_main_org
    missing_other_orgs = things - dashboards_other_orgs
    if not missing_main_org and not missing_other_orgs:
        logging.info("No missing dashboards")
        return False
    elif missing_main_org and not missing_other_orgs:
        logging.error(f"Missing dashboards (Main Org.): \n{missing_main_org}")
        return True
    elif not missing_main_org and missing_other_orgs:
        logging.error(f"Missing dashboards (Project Org.): \n{missing_other_orgs}")
        return True
    else:
        logging.error(f"Missing dashboards (Main Org.): \n{missing_main_org}")
        logging.error(f"Missing dashboards (Project Org.): \n{missing_other_orgs}")
        return True


if __name__ == "__main__":
    main()
