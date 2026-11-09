from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from constants import CustomJobType


class IngestScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cron_expression: str
    jitter_seconds: int
    enabled: bool
    updated_at: datetime
    next_runs: list[datetime] = []


class CustomJobRead(IngestScheduleRead):
    id: int
    job_type: CustomJobType
    ingest_id: Optional[int]  # None for project-wide jobs, which are read-only here
    params: dict
    note: Optional[str]


class IngestScheduleInfoRead(BaseModel):
    schedule: Optional[IngestScheduleRead] = None
    jobs: list[CustomJobRead] = []


class CustomJobParamSpec(BaseModel):
    name: str
    label: str
    type: str
    default: int
    minimum: int
    maximum: int


class CustomJobSpec(BaseModel):
    job_type: CustomJobType
    label: str
    description: str
    params: list[CustomJobParamSpec] = []


class CustomJobCreate(BaseModel):
    job_type: CustomJobType
    cron_expression: str
    jitter_seconds: Optional[int] = Field(
        default=None, ge=0, le=59, description="Random if omitted"
    )
    enabled: bool = True
    params: dict = {}
    note: Optional[str] = Field(default=None, max_length=200)


class CustomJobUpdate(BaseModel):
    cron_expression: Optional[str] = None
    jitter_seconds: Optional[int] = Field(default=None, ge=0, le=59)
    enabled: Optional[bool] = None
    params: Optional[dict] = None
    note: Optional[str] = Field(default=None, max_length=200)
