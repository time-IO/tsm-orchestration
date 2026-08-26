from datetime import datetime
from uuid import UUID
from fastapi_filters import FilterField, FilterSet


class BaseFilter(FilterSet):
    """Base filter class for most models."""

    id: FilterField[int]
    permission_group_id: FilterField[int]
    name: FilterField[str]
    uuid: FilterField[str]
    created_by_id: FilterField[int]
    created_at: FilterField[datetime]


class IngestFilter(FilterSet):
    """Ingest filter class for ingest models."""

    id: FilterField[int]
    permission_group_id: FilterField[int]
    name: FilterField[str]
    uuid: FilterField[str]
    created_by_id: FilterField[int]
    created_at: FilterField[datetime]
    ingest_type: FilterField[str]


class IngestExternalApiFilter(IngestFilter):
    api_type: FilterField[str]


class ParserDetailedFilter(FilterSet):
    id: FilterField[int]
    permission_group_id: FilterField[int]
    name: FilterField[str]
    uuid: FilterField[str]
    created_by_id: FilterField[int]
    created_at: FilterField[datetime]
    parser_type: FilterField[str]
