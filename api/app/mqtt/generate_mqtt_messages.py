def create_sync_ext_api_msg(ingest_uuid, date_from, date_to):
    msg = {
        "thing": str(ingest_uuid),
        "datetime_from": date_from,
        "datetime_to": date_to,
    }
    return msg


def create_sync_quality_control(
    permission_group_uuid, qc_settings_name, start_date, end_date
):
    msg = {
        "version": 2,
        "project_uuid": permission_group_uuid,
        "qc_settings_name": qc_settings_name,
        "start_date": start_date,
        "end_date": end_date,
    }
    return msg


def create_frontend_thing_update(ingest, ingest_type_info):
    permission_group = ingest.permission_group
    database = permission_group.database
    ingest_type = ingest_type_info["ingest_type"]
    msg = {
        "version": 7,
        "uuid": str(ingest.uuid),
        "name": ingest.name,
        "description": ingest.description,
        "ingest_type": ingest_type,
        "project": permission_group.mqtt_information,
        "database": database.mqtt_information,
    }
    if ingest_type == "extapi":
        msg["external_api"] = ingest.mqtt_information
    elif ingest_type == "sftp":
        msg["raw_data_storage"] = ingest.mqtt_information
        msg["parsers"] = ingest.csv_parser.mqtt_information
    elif ingest_type == "mqtt":
        msg["mqtt"] = ingest.mqtt_information
    elif ingest_type == "extsftp":
        msg["external_sftp"] = ingest.mqtt_information
        msg["raw_data_storage"] = ingest.mqtt_rawdatastorage
    return msg
