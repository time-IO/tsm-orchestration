#!/usr/bin/env python3

from __future__ import annotations
import os
import sys
import click
import requests

from dotenv import load_dotenv

load_dotenv()

# The TSMDL API currently provides no dedicated status endpoint.
# So the best way to check is pinging the tsmdl/Datasources endpoint via extra CLI argument
ENV_KEYS = [
    "PROXY_URL",
    "OBJECT_STORAGE_BROWSER_REDIRECT_URL",
    "VISUALIZATION_PROXY_URL",
    "STA_PROXY_URL",
    "THING_MANAGEMENT_PROXY_URL",
]


def get_env_endpoints():
    env_endpoints = [os.getenv(env_var) for env_var in ENV_KEYS]
    return env_endpoints


@click.command()
@click.option("--endpoint", "-e", multiple=True, help="Proxy endpoints to check")
def ping_endpoints(endpoint):
    dotenv_endpoints = get_env_endpoints()
    cli_endpoints = list(endpoint)
    endpoints = dotenv_endpoints + cli_endpoints

    if not endpoints:
        click.echo("No endpoints provided via dotenv file or cli")
        sys.exit(1)

    all_ok = True
    for url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            status = "ok"
        except requests.exceptions.HTTPError as http_err:
            status = f"HTTP error: {http_err.response.status_code}"
            all_ok = False
        except requests.exceptions.RequestException as e:
            status = f"Failed - {e}"
            all_ok = False

        click.echo(f"{url} --> {status}")

    click.echo("All services reachable!" if all_ok else "\nSome services failed.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    ping_endpoints()
