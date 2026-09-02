from fastapi_filters import FilterField

from .base_filters import BaseFilter


class QualityControlSettingFilter(BaseFilter):
    functions: FilterField[list[str]]
