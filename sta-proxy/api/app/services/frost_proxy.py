import logging

import anyio
import httpx
from fastapi import HTTPException, Response

from config import settings
from utils import (
    ensure_leading_slash,
    ensure_trailing_slash,
    remove_trailing_slash,
)
from services.permission_groups import get_own_permission_groups, has_internal_access

logger = logging.getLogger("app.services.frost_proxy")

EXCLUDED_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-encoding",
    "content-length",
    "server",
    "date",
}

# rewriting larger bodies in a worker thread keeps the event loop responsive
REWRITE_IN_THREAD_MIN_SIZE = 1_000_000


def is_json_response(upstream: httpx.Response) -> bool:
    """Check whether a FROST response has a JSON body.

    Args:
        upstream (httpx.Response): The response received from FROST.

    Returns:
        bool: ``True`` if the ``content-type`` header contains ``json``.
    """
    return "json" in upstream.headers.get("content-type", "").lower()


async def rewrite_links(content: bytes, old: bytes, new: bytes) -> bytes:
    """Replace all occurrences of a link prefix in a response body.

    This is a plain byte replacement. Bodies of at least
    ``REWRITE_IN_THREAD_MIN_SIZE`` bytes are processed in a worker
    thread so large responses do not block the event loop.

    Args:
        content (bytes): The response body.
        old (bytes): The prefix to replace.
        new (bytes): The replacement prefix.

    Returns:
        bytes: The body with all occurrences of ``old`` replaced by ``new``.
    """
    if len(content) < REWRITE_IN_THREAD_MIN_SIZE:
        return content.replace(old, new)
    return await anyio.to_thread.run_sync(content.replace, old, new)


class FrostServer:
    """A FROST server the proxy forwards requests to.

    Wraps a lazily created ``httpx.AsyncClient`` bound to the server's base
    URL and turns FROST responses into FastAPI responses. Responses from this
    class carry FROST's caching headers unchanged.

    Args:
        name (str): Name used in logs, e.g. ``"public"``.
        base_url (str): Base URL of the FROST server. A trailing slash is
            removed.
    """

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = remove_trailing_slash(base_url)
        self._client: httpx.AsyncClient | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, {self.base_url!r})"

    @property
    def client(self) -> httpx.AsyncClient:
        """httpx.AsyncClient: The shared client, recreated if missing or closed."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=settings.FROST_TIMEOUT
            )
        return self._client

    async def close(self) -> None:
        """Close the client, if one was created. Used on application shutdown."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(
        self, url: str, headers: dict[str, str], follow_redirects: bool = False
    ) -> httpx.Response:
        """Send a GET request to the FROST server.

        HTTP error statuses from FROST are not raised but returned, so they
        can be passed through to the client.

        Args:
            url (str): Path (and query) relative to ``base_url``.
            headers (dict[str, str]): Request headers to send.
            follow_redirects (bool): Whether to follow redirects.
                Defaults to ``False``.

        Returns:
            httpx.Response: The response from FROST, with any status code.

        Raises:
            HTTPException: 504 on a timeout, 502 if FROST is not reachable.
        """
        try:
            return await self.client.get(
                url, headers=headers, follow_redirects=follow_redirects
            )
        except httpx.TimeoutException:
            logger.warning("Timeout for %s FROST request %s", self.name, url)
            raise HTTPException(status_code=504, detail="FROST server timeout")
        except httpx.RequestError as e:
            logger.error("%s FROST request %s failed: %s", self.name, url, e)
            raise HTTPException(status_code=502, detail="FROST server not reachable")

    def get_filtered_headers(self, upstream: httpx.Response) -> dict[str, str]:
        """Select the FROST response headers to pass on to the client.

        Hop-by-hop headers and headers that no longer match the (possibly
        rewritten) body, such as ``content-length``, are dropped (see
        ``EXCLUDED_RESPONSE_HEADERS``). All other headers, including caching
        headers, are kept.

        Args:
            upstream (httpx.Response): The response received from FROST.

        Returns:
            dict[str, str]: The headers to send to the client.
        """
        return {
            k: v
            for k, v in upstream.headers.items()
            if k.lower() not in EXCLUDED_RESPONSE_HEADERS
        }

    def get_response_with_filtered_headers(
        self, upstream: httpx.Response, content: bytes
    ) -> Response:
        """Build the client response from a FROST response and a body.

        Args:
            upstream (httpx.Response): The response received from FROST,
                used for status code and headers.
            content (bytes): The body to send, possibly rewritten.

        Returns:
            Response: The response with FROST's status code and filtered
                headers.
        """
        return Response(
            content=content,
            status_code=upstream.status_code,
            headers=self.get_filtered_headers(upstream),
        )

    async def forward(
        self,
        url: str,
        headers: dict[str, str],
        link_rewrite: tuple[bytes, bytes] | None = None,
    ) -> Response:
        """Forward a request to FROST and return its response to the client.

        Args:
            url (str): Path (and query) relative to ``base_url``.
            headers (dict[str, str]): Request headers to send to FROST.
            link_rewrite (tuple[bytes, bytes] | None): ``(old, new)`` link
                prefixes to replace in JSON bodies, see ``get_link_rewrite``.
                Defaults to ``None`` (no rewrite).

        Returns:
            Response: The FROST response with filtered headers and possibly
                rewritten links.

        Raises:
            HTTPException: 504 or 502 if FROST cannot be reached, see
                ``fetch``.
        """
        upstream = await self.fetch(url, headers)
        logger.debug(
            "%s FROST responded with %s for %s", self.name, upstream.status_code, url
        )
        content = upstream.content
        if link_rewrite and is_json_response(upstream):
            content = await rewrite_links(content, *link_rewrite)
        return self.get_response_with_filtered_headers(upstream, content)


class InternalFrostServer(FrostServer):
    """A FROST server serving non-public data.

    Behaves like ``FrostServer``, but forbids any caching of its responses,
    so internal data is never stored.
    """

    def get_filtered_headers(self, upstream: httpx.Response) -> dict[str, str]:
        """Select the headers like ``FrostServer``, but force no caching.

        Args:
            upstream (httpx.Response): The response received from FROST.

        Returns:
            dict[str, str]: The headers to send to the client, with
            ``cache-control`` set to ``private, no-store``.
        """
        filtered_response_headers = super().get_filtered_headers(upstream)
        # no cache serving internal data
        filtered_response_headers["cache-control"] = "private, no-store"
        return filtered_response_headers


public_frost = FrostServer("public", settings.FROST_URL)
internal_frost = InternalFrostServer("internal", settings.FROST_INTERNAL_URL)
all_frost_servers = [public_frost, internal_frost]


async def close_frost_clients() -> None:
    """Close the clients of all FROST servers. Used on application shutdown."""
    for server in all_frost_servers:
        await server.close()


def get_endpoint_name_from_proxied_path(endpoint: str) -> str:
    """Extract the FROST endpoint name (first path segment) from a proxied path.

    The endpoint name identifies the project and is what access is checked
    against. Leading and trailing slashes are ignored.

    Args:
        endpoint (str): The proxied path.

    Returns:
        str: The first path segment, or ``""`` for an empty path.

    Examples:
        >>> get_endpoint_name_from_proxied_path("my_project/v1.1/Things")
        'my_project'
        >>> get_endpoint_name_from_proxied_path("/my_project/")
        'my_project'
    """
    return endpoint.strip("/").split("/", 1)[0]


def frost_service_root_url(endpoint_name: str) -> str:
    """Build the service root URL FROST generates for an endpoint.

    FROST generates its navigation links with ``settings.STA_PROXY_URL``
    as root, so this is the prefix found in its responses.

    Args:
        endpoint_name (str): The FROST endpoint name.

    Returns:
        str: ``STA_PROXY_URL`` followed by the endpoint name.
    """
    return f"{settings.STA_PROXY_URL}{endpoint_name}"


def get_link_rewrite(endpoint: str, route: str) -> tuple[bytes, bytes]:
    """Build the link rewrite that keeps clients on an explicit route.

    FROST generates links to the automatic route (``<root>/<name>/...``).
    Responses served via ``/public`` or ``/internal`` rewrite them to
    ``<root>/<route>/<name>/...``.

    Args:
        endpoint (str): The proxied path, used to get the endpoint name.
        route (str): The explicit route, ``"public"`` or ``"internal"``.

    Returns:
        tuple[bytes, bytes]: The ``(old, new)`` link prefixes, see
        ``rewrite_links``.
    """
    root = ensure_trailing_slash(settings.STA_PROXY_URL)
    endpoint_name = get_endpoint_name_from_proxied_path(endpoint)
    return (
        f"{frost_service_root_url(endpoint_name)}/".encode(),
        f"{root}{route}/{endpoint_name}/".encode(),
    )


async def require_internal_access(endpoint: str, authorization: str | None) -> None:
    """Ensure the caller may read internal data of the addressed endpoint.

    Access is granted if the caller has a permission group named like the
    endpoint. Permission groups are looked up in the DSM API and cached.

    Args:
        endpoint (str): The proxied path, used to get the endpoint name.
        authorization (str | None): The caller's ``Authorization`` value.

    Raises:
        HTTPException: 401 without credentials or if the DSM API rejects
            them, 403 without a matching permission group, 502 or 504 if
            the DSM API lookup fails.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    endpoint_name = get_endpoint_name_from_proxied_path(endpoint)
    permission_groups = await get_own_permission_groups(authorization)
    if not has_internal_access(endpoint_name, permission_groups):
        logger.debug("Denied internal access to %s", endpoint)
        raise HTTPException(status_code=403, detail="No access to internal endpoint")


async def select_frost_server_by_authorization(
    endpoint: str, authorization: str | None
) -> FrostServer:
    """Choose the FROST server for the automatic route.

    Callers with access to the endpoint get internal data, everyone else
    public data. Failing access results in silent fallback to the public
    server.

    Args:
        endpoint (str): The proxied path.
        authorization (str | None): The caller's ``Authorization`` value.

    Returns:
        FrostServer: ``internal_frost`` if access is granted, otherwise
        ``public_frost``.
    """
    if not authorization:
        return public_frost
    try:
        await require_internal_access(endpoint, authorization)
    except HTTPException as e:
        if e.status_code != 403:
            logger.warning("Checking internal access failed: %s", e.detail)
        return public_frost
    # user is authorized and has required permission group
    return internal_frost


async def forward_to_frost(
    server: FrostServer,
    endpoint: str,
    query: str,
    accept: str | None,
    link_rewrite: tuple[bytes, bytes] | None = None,
) -> Response:
    """Forward a proxied request to a FROST server.

    Only the path, the query string and the ``Accept`` header are forwarded;
    the caller's credentials are never sent to FROST.

    Args:
        server (FrostServer): The FROST server to forward to.
        endpoint (str): The proxied path that should have been checked with
            ``validate_proxied_path``
        query (str): The raw query string, forwarded unchanged.
        accept (str | None): The caller's ``Accept`` header.
        link_rewrite (tuple[bytes, bytes] | None): Link prefixes to rewrite,
            see ``get_link_rewrite``. Defaults to ``None``.

    Returns:
        Response: The FROST response.

    Raises:
        HTTPException: 504 or 502 if FROST cannot be reached.
    """
    url = ensure_leading_slash(endpoint)
    if query:
        url += "?" + query

    headers = {"accept": accept} if accept else {}
    logger.debug("Forwarding %s to %s FROST", endpoint, server.name)
    return await server.forward(url, headers, link_rewrite)


async def frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
    authorization: str | None = None,
) -> Response:
    """Serve the automatic route: internal data if permitted, else public data.

    ``Vary: Authorization, Cookie`` is added so caches keep separate copies
    per caller. Links are not rewritten.

    Args:
        endpoint (str): The validated proxied path.
        query (str): The raw query string. Defaults to ``""``.
        accept (str | None): The caller's ``Accept`` header.
            Defaults to ``None``.
        authorization (str | None): The caller's ``Authorization`` value.
            Defaults to ``None``.

    Returns:
        Response: The response of the selected FROST server.

    Raises:
        HTTPException: 504 or 502 if FROST cannot be reached.
    """
    server = await select_frost_server_by_authorization(endpoint, authorization)
    response = await forward_to_frost(server, endpoint, query, accept)
    # the selected server depends on the authorization, caches must respect it
    # see https://developer.mozilla.org/de/docs/Web/HTTP/Reference/Headers/Vary
    response.headers["vary"] = ", ".join(
        v for v in (response.headers.get("vary"), "Authorization, Cookie") if v
    )
    return response


async def public_frost_proxy_service(
    endpoint: str, query: str = "", accept: str | None = None
) -> Response:
    """Serve the explicit ``/public`` route from the public FROST server.

    Links in JSON responses are rewritten to the ``/public`` route.

    Args:
        endpoint (str): The validated proxied path.
        query (str): The raw query string. Defaults to ``""``.
        accept (str | None): The caller's ``Accept`` header.
            Defaults to ``None``.

    Returns:
        Response: The public FROST response.

    Raises:
        HTTPException: 504 or 502 if FROST cannot be reached.
    """
    return await forward_to_frost(
        public_frost, endpoint, query, accept, get_link_rewrite(endpoint, "public")
    )


async def internal_frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
    authorization: str | None = None,
) -> Response:
    """Serve the explicit ``/internal`` route from the internal FROST server.

    No fallback to public data. Links in JSON responses are rewritten to the
    ``/internal`` route.

    Args:
        endpoint (str): The validated proxied path.
        query (str): The raw query string. Defaults to ``""``.
        accept (str | None): The caller's ``Accept`` header.
            Defaults to ``None``.
        authorization (str | None): The caller's ``Authorization`` value.
            Defaults to ``None``.

    Returns:
        Response: The internal FROST response, marked as not cacheable.

    Raises:
        HTTPException: 401, 403, 502 or 504 if access is denied or cannot be
            checked (see ``require_internal_access``), 504 or 502 if FROST
            cannot be reached.
    """
    await require_internal_access(endpoint, authorization)
    return await forward_to_frost(
        internal_frost, endpoint, query, accept, get_link_rewrite(endpoint, "internal")
    )
