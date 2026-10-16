import logging

import httpx
from fastapi import HTTPException, Response

from config import settings

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

    def get_filtered_headers_response(self, upstream: httpx.Response) -> Response:
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=self.get_filtered_headers(upstream),
        )

    async def forward(self, url: str, headers: dict[str, str]) -> Response:
        upstream = await self.fetch(url, headers)
        logger.debug(
            "%s FROST responded with %s for %s", self.name, upstream.status_code, url
        )
        return self.get_filtered_headers_response(upstream)


public_frost = FrostServer("public", settings.FROST_URL)
all_frost_servers = [public_frost]


async def close_frost_clients() -> None:
    for server in all_frost_servers:
        await server.close()


async def frost_proxy_service(
    endpoint: str,
    query: str = "",
    accept: str | None = None,
) -> Response:
    url = "/" + endpoint
    if query:
        url += "?" + query

    headers = {"accept": accept} if accept else {}
    return await public_frost.forward(url, headers)
