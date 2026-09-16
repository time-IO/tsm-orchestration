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
    ALLOWED_ORIGINS: str = ""
    MINIO_SFTP_PORT: str
    S3_ENDPOINT: str = ""
    S3_SECURE: bool = False
    S3_REGION: str = "eu-central-1"
    PROXY_URL: str
    FERNET_ENCRYPTION_SECRET: str
    STA_ROOT_URL: str
    STA_VERSION: str
    MQTT_BROKER_HOST: str
    MQTT_PORT: int = 1883
    MQTT_CLIENT_ID: str
    MQTT_USER: str
    MQTT_PASSWORD: str
    MQTT_QOS: int = 2
    INGEST_MQTT_BROKER_URI: str
    DB_API_BASE_URL: str = ""
    DB_API_AUTH_TOKEN: str = ""

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ALLOWED_ORIGINS_LIST(self) -> list[str]:
        if not self.ALLOWED_ORIGINS:
            return []
        return [vo.strip() for vo in self.ALLOWED_ORIGINS.split(",") if vo.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SFTP_URI(self) -> str:
        if not self.MINIO_SFTP_PORT or not self.PROXY_URL:
            return ""
        sftp_port = self.MINIO_SFTP_PORT.split(":")[-1]
        proxy = self.PROXY_URL.split("://")[-1].split(":")[0]

        return f"sftp://{proxy}:{sftp_port}"


settings = Settings()  # type: ignore
