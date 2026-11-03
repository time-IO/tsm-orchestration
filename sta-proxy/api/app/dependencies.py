from fastapi import Header, Request

from config import settings


def get_authorization(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str | None:
    # browser navigation cannot send a bearer token; fall back to the session cookie
    if not authorization:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if token:
            authorization = f"Bearer {token}"
    return authorization
