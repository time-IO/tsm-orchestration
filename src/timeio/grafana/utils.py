from __future__ import annotations

from typing import List, Dict, Any
from grafana_client.client import GrafanaException


def get_dict_by_key_value(dict_list: List[Dict], key: str, value: Any):
    for d in dict_list:
        if d.get(key) == value:
            return d
    return None


def _exists(func: callable, *args) -> bool:
    try:
        func(*args)
    except GrafanaException:
        return False
    else:
        return True
