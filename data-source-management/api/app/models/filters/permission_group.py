from fastapi_filters import FilterSet, FilterField


class PermissionGroupFilter(FilterSet):
    id = FilterField[int]
    name = FilterField[str]
