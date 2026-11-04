from typing import Literal
from pydantic import BaseModel

from .date_range import DateRangeBase


class TriggerReparseBase(DateRangeBase):
    ingest_id: int
    filename_pattern: str | None = None
    parser_id: int | None = None
    include_parsed: bool = False
    parsed_files_parser: Literal["current", "original"] = "current"


class TriggerReparseResponse(BaseModel):
    triggered_ingest: int
