from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    ALLOWED_ORIGINS: str = ""
    FROST_URL: str = "http://frost:8080"
    FROST_TIMEOUT: float = 30.0
    FROST_ENDPOINTS_PATH: str = "/"
    BASE_URL: str = "http://localhost"
    DSM_API_URL: str = "http://dsm-api:8000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ALLOWED_ORIGINS_LIST(self) -> list[str]:
        if not self.ALLOWED_ORIGINS:
            return []
        return [vo.strip() for vo in self.ALLOWED_ORIGINS.split(",") if vo.strip()]


settings = Settings()  # type: ignore
