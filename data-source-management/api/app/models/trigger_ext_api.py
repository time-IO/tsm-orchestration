from pydantic import BaseModel
from typing import List


class TriggerSyncExtApiBase(BaseModel):
    ingest_ids: List[int]
    start_date: str
    end_date: str


class TriggerSyncExtApiResponse(BaseModel):
    triggered_ingests: List[int]
