from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    FROST_URL: str = "http://frost:8080"
    FROST_TIMEOUT: float = 120.0
    FROST_ENDPOINTS_PATH: str = "/"
    BASE_URL: str = "http://localhost"
    DSM_API_URL: str = "http://dsm-api:8000"
    DSM_API_TIMEOUT: float = 30.0


settings = Settings()  # type: ignore
