from fastapi_filters import FilterSet, FilterField


class MqttParserFilter(FilterSet):
    id: FilterField[int]
    name: FilterField[str]
