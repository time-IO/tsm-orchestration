#!/usr/bin/env python3
from __future__ import annotations

import logging
from urllib.parse import urlparse, urlunparse

import requests

from timeio.crypto import decrypt, get_crypt_key

logger = logging.getLogger(__name__)


def push_context(
    api_url: str, token: str, schema: str, user: str, password: str, db_url: str
) -> None:
    """PUT a context's DB connection to a FROST context API; `password` is encrypted."""
    parts = urlparse(db_url)
    hostname = parts.hostname
    if parts.port:
        hostname += f":{parts.port}"
    url = f"{api_url.rstrip('/')}/contexts/{schema}"
    logger.debug(f"push tomcat context {schema!r} to {url!r}")
    resp = requests.put(
        url,
        data={
            "user": user,
            "password": decrypt(password, get_crypt_key()),
            "url": urlunparse((parts.scheme, hostname, parts.path, "", "", "")),
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if not resp.ok:
        # the API's error body names the rejected field
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} for {url}: {resp.text[:200]}",
            response=resp,
        )
