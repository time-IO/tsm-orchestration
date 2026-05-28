from typing import Optional
from fastapi import HTTPException


def parse_sort_param(sort_param: Optional[str]) -> tuple[str, str]:
    if not sort_param:
        return None, None
    parts = sort_param.split(":")
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail="Sort parameter must be in format 'field:asc' or 'field:desc' (e.g., 'name:asc')",
        )
    field_name, order = parts[0].strip(), parts[1].strip().lower()
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Sort order must be 'asc' or 'desc'",
        )
    return field_name, order


def _get_sort_value(item, field_name: str):
    if isinstance(item, dict):
        value = item.get(field_name)
    else:
        value = getattr(item, field_name, None)
    if field_name == "permission_group":
        if isinstance(value, dict):
            return value.get("name")
        return getattr(value, "name", None)
    return value


def apply_sort_list(items: list, sort_param: Optional[str]) -> list:
    # If no sort_param is provided or the list is empty, return the original list
    if not sort_param or not items:
        return items
    field_name, order = parse_sort_param(sort_param)
    reverse = order == "desc"

    def sort_key(item):
        value = _get_sort_value(item, field_name)
        # Avoid comparing dict/object values directly.
        if not isinstance(value, (type(None), str, int, float, bool)):
            value = str(value)
        # Keep non-existing values grouped consistently.
        return value is None, value

    return sorted(
        items,
        key=sort_key,
        reverse=reverse,
    )
