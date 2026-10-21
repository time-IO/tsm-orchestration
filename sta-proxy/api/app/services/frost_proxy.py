import logging

import anyio
import httpx
from fastapi import HTTPException, Response

from config import settings
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
    return "json" in upstream.headers.get("content-type", "").lower()


async def rewrite_links(content: bytes, old: bytes, new: bytes) -> bytes:
    if len(content) < REWRITE_IN_THREAD_MIN_SIZE:
        return content.replace(old, new)
    return await anyio.to_thread.run_sync(content.replace, old, new)


class FrostServer:
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, {self.base_url!r})"

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=settings.FROST_TIMEOUT
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str, headers: dict[str, str]) -> httpx.Response:
        try:
            return await self.client.get(url, headers=headers)
        except httpx.TimeoutException:
            logger.warning("Timeout for %s FROST request %s", self.name, url)
            raise HTTPException(status_code=504, detail="FROST server timeout")
        except httpx.RequestError as e:
            logger.error("%s FROST request %s failed: %s", self.name, url, e)
            raise HTTPException(status_code=502, detail="FROST server not reachable")

    def get_filtered_headers(self, upstream: httpx.Response) -> dict[str, str]:
        return {
            k: v
            for k, v in upstream.headers.items()
            if k.lower() not in EXCLUDED_RESPONSE_HEADERS
        }

    def get_filtered_headers_response(
        self, upstream: httpx.Response, content: bytes
    ) -> Response:
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
        upstream = await self.fetch(url, headers)
        logger.debug(
            "%s FROST responded with %s for %s", self.name, upstream.status_code, url
        )
        content = upstream.content
        if link_rewrite and is_json_response(upstream):
            content = await rewrite_links(content, *link_rewrite)
        return self.get_filtered_headers_response(upstream, content)


class InternalFrostServer(FrostServer):
    def get_filtered_headers(self, upstream: httpx.Response) -> dict[str, str]:
        filtered_response_headers = super().get_filtered_headers(upstream)
        # no cache serving internal data
        filtered_response_headers["cache-control"] = "private, no-store"
        return filtered_response_headers


public_frost = FrostServer("public", settings.FROST_URL)
internal_frost = InternalFrostServer("internal", settings.FROST_INTERNAL_URL)
all_frost_servers = [public_frost, internal_frost]


async def close_frost_clients() -> None:
    for server in all_frost_servers:
        await server.close()


def get_endpoint_name_from_proxied_path(endpoint: str) -> str:
    return endpoint.strip("/").split("/", 1)[0]


def frost_service_root_url(endpoint_name: str) -> str:
    return f"{settings.STA_PROXY_URL}{endpoint_name}"


def get_link_rewrite(endpoint: str, route: str) -> tuple[bytes, bytes]:
    """Adjust generated FROST navigation links to explicit routes."""
    root = settings.STA_PROXY_URL.rstrip("/") + "/"
    endpoint_name = get_endpoint_name_from_proxied_path(endpoint)
    return (
        f"{frost_service_root_url(endpoint_name)}/".encode(),
        f"{root}{route}/{endpoint_name}/".encode(),
    )


async def require_internal_access(endpoint: str, authorization: str | None) -> None:
    """Raises 401/403 without access, or the DSM API error if the lookup fails."""
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
    url = "/" + endpoint
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
    return await forward_to_frost(
        public_frost, endpoint, query, accept, get_link_rewrite(endpoint, "public")
    )


async def internal_frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
    authorization: str | None = None,
) -> Response:
    await require_internal_access(endpoint, authorization)
    return await forward_to_frost(
        internal_frost, endpoint, query, accept, get_link_rewrite(endpoint, "internal")
    )
