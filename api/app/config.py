from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, computed_field


class Settings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    OIDC_WELL_KNOWN: str
    OIDC_ISSUER: str
    OIDC_AUDIENCE: str
    ALLOWED_VOS: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ALLOWED_VOS_LIST(self) -> list[str]:
        if not self.ALLOWED_VOS:
            return []
        return [vo.strip() for vo in self.ALLOWED_VOS.split(",") if vo.strip()]


settings = Settings()  # type: ignore
