from fastapi import HTTPException

from config import settings

AMBIGUOUS_PATH_CHARS = (";", "%", "\\")


def validate_proxied_path(endpoint: str) -> None:
    """Reject proxied paths that could be interpreted differently downstream.

    The access check and the request forwarded to FROST must agree on which
    endpoint (first path segment) is addressed. Paths that a proxy, Tomcat or
    httpx could resolve differently than the access check are therefore
    rejected initially.

    Args:
        endpoint (str): The proxied path as received by the route, i.e.
            everything after the route prefix (already URL-decoded).

    Raises:
        HTTPException: 400 if the path contains ``.`` or ``..`` segments, one
            of the characters in ``AMBIGUOUS_PATH_CHARS``, or an empty segment
            other than the first or last one (e.g. ``//a/b`` or ``a//b``, which
            httpx would read as a host name). 404 if the path addresses the
            FROST endpoint listing (``settings.FROST_ENDPOINTS_PATH``), which
            is only exposed via the dedicated endpoints route.

    Examples:
        >>> validate_proxied_path("my_project/v1.1/Things")
        >>> validate_proxied_path("my_project/../other/v1.1")
        Traceback (most recent call last):
        ...
        fastapi.exceptions.HTTPException: 400: Invalid path
        >>> validate_proxied_path("//my_project/other/v1.1")
        Traceback (most recent call last):
        ...
        fastapi.exceptions.HTTPException: 400: Invalid path
    """
    # reject path traversal
    segments = endpoint.split("/")
    if any(s in (".", "..") for s in segments) or any(
        c in endpoint for c in AMBIGUOUS_PATH_CHARS
    ):
        raise HTTPException(status_code=400, detail="Invalid path")

    # hide FROST endpoint listing
    if endpoint.strip("/") == settings.FROST_ENDPOINTS_PATH.strip("/"):
        raise HTTPException(status_code=404, detail="Not Found")

    # reject inner empty segments (e.g. "//a/b")
    # httpx reads a segment after "//" as host name and therefore drops it.
    # e. g. "//my_endpoint/foreign_endpoint" would drop "my_endpoint" and
    # redirect to "foreign_endpoint" without any further permission checks
    if "" in segments[1:-1]:
        raise HTTPException(status_code=400, detail="Invalid path")


def remove_trailing_slash(value: str) -> str:
    """Remove a single trailing slash from a string, if present.

    Only the last character is checked, so of multiple trailing slashes
    only one is removed. Strings without a trailing slash are returned
    unchanged.

    Args:
        value (str): The string, typically a URL or path.

    Returns:
        str: ``value`` without its trailing slash.

    Examples:
        >>> remove_trailing_slash("http://example.org/")
        'http://example.org'
        >>> remove_trailing_slash("http://example.org")
        'http://example.org'
        >>> remove_trailing_slash("a//")
        'a/'
        >>> remove_trailing_slash("/")
        ''
    """
    if value.endswith("/"):
        return value[:-1]
    return value


def ensure_trailing_slash(value: str) -> str:
    """Append a trailing slash to a string, if missing.

    Strings that already end with a slash are returned unchanged, so
    multiple trailing slashes are not collapsed.

    Args:
        value (str): The string, typically a URL or path.

    Returns:
        str: ``value`` ending with ``/``.

    Examples:
        >>> ensure_trailing_slash("http://example.org/path")
        'http://example.org/path/'
        >>> ensure_trailing_slash("http://example.org/path/")
        'http://example.org/path/'
        >>> ensure_trailing_slash("")
        '/'
    """
    if value.endswith("/"):
        return value
    return value + "/"


def ensure_leading_slash(value: str) -> str:
    """Prepend a leading slash to a string, if missing.

    Strings that already start with a slash are returned unchanged.

    Note: Multiple leading slashes are not collapsed.

    Args:
        value (str): The string, typically a path.

    Returns:
        str: ``value`` starting with ``/``.

    Examples:
        >>> ensure_leading_slash("some/path")
        '/some/path'
        >>> ensure_leading_slash("/some/path")
        '/some/path'
        >>> ensure_leading_slash("")
        '/'
    """
    if value.startswith("/"):
        return value
    return "/" + value
