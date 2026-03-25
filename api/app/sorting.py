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


def apply_sort_list(items: list, sort_param: Optional[str]) -> list:
    # If no sort_param is provided or the list is empty, return the original list
    if not sort_param or not items:
        return items
    field_name, order = parse_sort_param(sort_param)
    reverse = order == "desc"
    return sorted(
        items,
        key=lambda item: getattr(item, field_name, ""),
        reverse=reverse,
    )
