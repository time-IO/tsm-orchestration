from pydantic import field_validator
from pydantic_settings import BaseSettings

from utils import ensure_trailing_slash


class Settings(BaseSettings):
    FROST_URL: str = "http://frost:8080"
    FROST_INTERNAL_URL: str = "http://frost-internal:8080"
    FROST_TIMEOUT: float = 120.0
    FROST_ENDPOINTS_PATH: str = "/"
    BASE_URL: str = "http://localhost"
    STA_HUB_URL: str = "http://localhost/sta/"
    DSM_API_URL: str = "http://dsm-api:8000"
    DSM_API_TIMEOUT: float = 30.0
    PERMISSION_GROUPS_CACHE_TTL: float = 60.0
    PERMISSION_GROUPS_CACHE_SIZE: int = 1024
    SESSION_COOKIE_NAME: str = "sta_session"
    SESSION_COOKIE_PATH: str = "/sta/"

    @field_validator("STA_HUB_URL")
    @classmethod
    def ensure_sta_hub_url_trailing_slash(cls, value: str) -> str:
        return ensure_trailing_slash(value)


settings = Settings()  # type: ignore
