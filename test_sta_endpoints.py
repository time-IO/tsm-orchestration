#!/usr/bin/env python3

from __future__ import annotations
import sys
import os
import click
import requests
import psycopg

from dotenv import load_dotenv

load_dotenv()
sta_base_url = os.environ.get("STA_PROXY_URL")
configdb_dsn = os.environ.get("CONFIGDB_READONLY_DSN")


def get_all_projects():
    with psycopg.connect(configdb_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT "schema" from "database"')
            rows = cur.fetchall()
    return [row[0] for row in rows]


sta_endpoints = [
    "Things",
    "Sensors",
    "ObservedProperties",
    "Observations",
    "Locations",
    "HistoricalLocations",
    "FeaturesOfInterest",
    "Datastreams",
]


def ping_sta_endpoints(project: str):
    all_ok = True
    failed_endpoints = []
    for endpoint in sta_endpoints:
        url = f"{sta_base_url}{project}/v1.1/{endpoint}"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            status = "ok"
        except requests.exceptions.HTTPError as http_err:
            status = f"HTTP error: {http_err.response.status_code}"
            all_ok = False
            failed_endpoints.append(endpoint)
        except requests.exceptions.RequestException as e:
            status = f"Failed - {e}"
            all_ok = False
            failed_endpoints.append(endpoint)
        click.echo(f"{url} --> {status}")
    return all_ok, {project: failed_endpoints}


@click.command()
def main():
    all_projects_ok = True
    failures = []
    for project in get_all_projects():
        click.echo(f"\nChecking project: {project}")
        project_ok, failed_ep = ping_sta_endpoints(project)
        if not project_ok:
            all_projects_ok = False
            failures.append(failed_ep)
    click.echo(
        "\nAll endpoints are reachable for every projects."
        if all_projects_ok
        else f"\nThe following endpoints are not reachable: {failures}"
    )
    sys.exit(0 if all_projects_ok else 1)


if __name__ == "__main__":
    main()
