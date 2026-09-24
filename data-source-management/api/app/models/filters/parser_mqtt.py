from fastapi_filters import FilterSet, FilterField


class ParserMqttFilter(FilterSet):
    id: FilterField[int]
    name: FilterField[str]
