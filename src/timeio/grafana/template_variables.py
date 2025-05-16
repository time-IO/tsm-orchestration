def datastream_sql(uid: str) -> str:
    return f"""SELECT property FROM datastream_properties WHERE t_uuid::text = '{uid}'"""

def datastream_templating():
    datastream_template = {
        "datasource": datasource,
        "hide": 0,
        "includeAll": True,
        "label": "Datastream",
        "multi": True,
        "name": "datastream_pos",
        "query": datastream_sql(uid),
        "refresh": 1,
        "sort": 7,
        "type": "query",
    }
    return datastream_template

show_qaqc_templating = {
    "datasource": datasource,
    "hide": 0,
    "type": "custom",
    "name": "show_qaqc_flags",
    "label": "Show QAQC Flags",
    "query": "False,True",
    "multi": False,
    "includeAll": False,
    "options": [
        {"text": "False", "value": "False", "selected": True},
        {"text": "True", "value": "True", "selected": False},
    ],
}