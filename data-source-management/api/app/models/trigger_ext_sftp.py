from pydantic import BaseModel

from .date_range import DateRangeBase


class TriggerSyncExtSftpBase(DateRangeBase):
    ingest_id: int


class TriggerSyncExtSftpResponse(BaseModel):
    triggered_ingest: int
