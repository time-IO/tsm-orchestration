from datetime import datetime
from uuid import UUID
from fastapi_filters import FilterField, FilterSet


class BaseFilter(FilterSet):
    """Base filter class for most models."""

    id: FilterField[int]
    permission_group_id: FilterField[int]
    name: FilterField[str]
    uuid: FilterField[UUID]
    created_by_id: FilterField[int]
    created_at: FilterField[datetime]


class ExternalApiBaseFilter(BaseFilter):
    """Base filter class for external API models."""

    sync_interval_in_minutes: FilterField[int]
    sync_enabled: FilterField[bool]
