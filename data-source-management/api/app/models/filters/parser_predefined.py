from fastapi_filters import FilterSet, FilterField


class ParserPredefinedFilter(FilterSet):
    id: FilterField[int]
    name: FilterField[str]
