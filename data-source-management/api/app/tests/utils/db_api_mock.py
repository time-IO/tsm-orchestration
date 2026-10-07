from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx

BASE_URL = "http://db-api:8001"
AUTH_TOKEN = "test-token"


def thing_path(thing_uuid: UUID | str, resource: str) -> str:
    return f"/things/{thing_uuid}/{resource}"


@dataclass(frozen=True)
class RecordedRequest:
    method: str
    path: str
    params: dict[str, str]
    headers: httpx.Headers
    body: Any | None

    @property
    def authorization(self) -> str | None:
        return self.headers.get("authorization")


class FakeDbApi:
    def __init__(self, base_url: str = BASE_URL, token: str = AUTH_TOKEN) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.requests: list[RecordedRequest] = []
        self._responses: dict[tuple[str, str], httpx.Response] = {}

    @property
    def expected_authorization(self) -> str:
        return f"Bearer {self.token}"

    def stub(
        self,
        path: str,
        *,
        json: Any = None,
        status_code: int = 200,
        method: str = "GET",
    ) -> None:
        self._responses[(method.upper(), path)] = httpx.Response(status_code, json=json)

    def stub_thing(
        self,
        thing_uuid: UUID | str,
        resource: str,
        *,
        json: Any = None,
        status_code: int = 200,
    ) -> None:
        self.stub(thing_path(thing_uuid, resource), json=json, status_code=status_code)

    @property
    def last_request(self) -> RecordedRequest:
        assert self.requests, "FakeDbApi received no requests"
        return self.requests[-1]

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(
            RecordedRequest(
                method=request.method,
                path=request.url.path,
                params=dict(request.url.params),
                headers=request.headers,
                body=_decode_body(request.content),
            )
        )

        stubbed = self._responses.get((request.method, request.url.path))
        if stubbed is None:
            return httpx.Response(
                404,
                json={
                    "detail": f"FakeDbApi: no stub for {request.method} {request.url.path}"
                },
            )

        return httpx.Response(
            stubbed.status_code, content=stubbed.content, headers=stubbed.headers
        )


def _decode_body(content: bytes) -> Any | None:
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content
