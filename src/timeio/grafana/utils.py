from __future__ import annotations

from typing import List, Dict, Any
from grafana_client.client import GrafanaException

def value_from_dict_list(dict_list: List[Dict], key: str, value: Any):
    for d in dict_list:
        if d.get(key) == value:
            return d
    return None

def _exists(self, func: callable, *args) -> bool:
    try:
        func(*args)
    except GrafanaException:
        return False
    else:
        return True