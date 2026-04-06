from fastapi_filters import FilterSet
from .base_filters import ExternalApiBaseFilter


class NeutronMonitorStationFilter(FilterSet): ...


class IngestExternalApiNeutronMonitorFilter(ExternalApiBaseFilter): ...
