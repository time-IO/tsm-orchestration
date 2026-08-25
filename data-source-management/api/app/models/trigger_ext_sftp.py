from pydantic import BaseModel


class TriggerSyncExtSftpBase(BaseModel):
    ingest_id: int
    start_date: str | None = None
    end_date: str | None = None


class TriggerSyncExtSftpResponse(BaseModel):
    triggered_ingest: int
