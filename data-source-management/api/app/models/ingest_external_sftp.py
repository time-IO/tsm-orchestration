from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional
from encryption import EncryptedType
from .ingest import Ingest, IngestRead, IngestCreate, IngestUpdate


class IngestExternalSftpRead(IngestRead):
    parser_id: int
    uri: str
    path: str
    username: Optional[str]
    password: Optional[str]
    bucket_username: str
    bucket_password: str
    sync_interval_in_minutes: Optional[int]
    sync_enabled: bool
    filename_pattern: str
    parser: dict
    ssh_public_key: str


class IngestExternalSftpCreate(IngestCreate):
    parser_id: int
    uri: str
    path: str
    filename_pattern: str
    username: Optional[str] = None
    password: Optional[str] = None
    sync_interval_in_minutes: Optional[int] = None
    sync_enabled: bool = False


class IngestExternalSftpUpdate(IngestUpdate):
    uri: Optional[str] = None
    path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sync_interval_in_minutes: Optional[int] = None
    sync_enabled: Optional[bool] = None
    filename_pattern: Optional[str] = None


class IngestExternalSftp(SQLModel, table=True):
    __tablename__ = "ingest_external_sftp"

    ingest_id: int = Field(
        foreign_key="ingest.id", primary_key=True, ondelete="CASCADE"
    )

    uri: str
    path: str
    filename_pattern: str
    username: Optional[str] = None
    password: Optional[str] = Field(
        sa_column=Column("password", EncryptedType, nullable=True)
    )

    sync_interval_in_minutes: Optional[int] = Field(ge=10, nullable=True)
    sync_enabled: bool = False

    ssh_private_key: str = Field(
        sa_column=Column("ssh_private_key", EncryptedType, nullable=True)
    )
    ssh_public_key: str

    bucket_name: str
    bucket_username: str
    bucket_password: str = Field(
        sa_column=Column("bucket_password", EncryptedType, nullable=False)
    )

    ingest: Ingest = Relationship(back_populates="external_sftp_detail")

    @property
    def parser_information(self):
        return self.ingest.parser.mqtt_information

    @property
    def ingest_type(self):
        return self.ingest.ingest_type

    @property
    def permission_group(self):
        return self.ingest.permission_group

    @property
    def uuid(self):
        return self.ingest.uuid

    @property
    def name(self):
        return self.ingest.name

    @property
    def description(self):
        return self.ingest.description
