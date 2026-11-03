from fastapi import HTTPException

from config import settings

AMBIGUOUS_PATH_CHARS = (";", "%", "\\")


def validate_proxied_path(endpoint: str) -> None:
    # reject path traversal
    segments = endpoint.split("/")
    if any(s in (".", "..") for s in segments) or any(
        c in endpoint for c in AMBIGUOUS_PATH_CHARS
    ):
        raise HTTPException(status_code=400, detail="Invalid path")

    # hide FROST endpoint listing
    if endpoint.strip("/") == settings.FROST_ENDPOINTS_PATH.strip("/"):
        raise HTTPException(status_code=404, detail="Not Found")
