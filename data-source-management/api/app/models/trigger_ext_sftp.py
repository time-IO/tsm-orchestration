from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class TriggerSyncExtSftpBase(BaseModel):
    ingest_id: int
    start_date: str | None = None
    end_date: str | None = None

    @field_validator("start_date", "end_date")
    @classmethod
    def _validate_isoformat(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(
                "must be an ISO-8601 datetime (e.g. 'YYYY-MM-DD' or "
                "'YYYY-MM-DD HH:MM:SS')"
            )
        return value

    @model_validator(mode="after")
    def _validate_order(self) -> "TriggerSyncExtSftpBase":
        if self.start_date and self.end_date:
            if datetime.fromisoformat(self.start_date) >= datetime.fromisoformat(
                self.end_date
            ):
                raise ValueError("end_date must be after start_date")
        return self


class TriggerSyncExtSftpResponse(BaseModel):
    triggered_ingest: int
