from fastapi_filters import FilterField

from .base_filters import BaseFilter


class CsvParserFilter(BaseFilter):
    permission_group_id: FilterField[int]
    header: FilterField[int]
