from fastapi import Header, Request

from config import settings


def get_authorization(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str | None:
    """Resolve the caller's credentials from the header or the session cookie.

    FastAPI dependency. API clients send a bearer token in the
    ``Authorization`` header, but browser navigation (e.g. opening a FROST
    link) cannot. For those requests the token stored in the session cookie
    is used instead. The header takes precedence. The value is not validated
    here.

    Args:
        request (Request): The incoming request, used to read the cookie.
        authorization (str | None): The ``Authorization`` header.
            Defaults to ``None``.

    Returns:
        str | None: The ``Authorization`` header, ``"Bearer <token>"`` built
        from the session cookie, or ``None`` if neither is present.
    """
    # browser navigation cannot send a bearer token; fall back to the session cookie
    if not authorization:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if token:
            authorization = f"Bearer {token}"
    return authorization
