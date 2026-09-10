from constants import IngestType


def create_sync_ext_api_msg(ingest_uuid, date_from, date_to):
    msg = {
        "thing": str(ingest_uuid),
        "datetime_from": date_from,
        "datetime_to": date_to,
    }
    return msg


def create_sync_ext_sftp_msg(ingest_uuid, datetime_from, datetime_to):
    msg = {"thing": str(ingest_uuid)}
    if datetime_from is not None:
        msg["datetime_from"] = datetime_from
    if datetime_to is not None:
        msg["datetime_to"] = datetime_to
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


def create_frontend_thing_update(ingest):
    msg = {"version": 8, "thing": str(ingest.uuid)}
    return msg


def create_qc_settings_msg(qc_setting):
    msg = {
        "version": 3,
        "default": qc_setting.is_active,
        "project_uuid": str(qc_setting.permission_group.uuid),
        "name": qc_setting.name,
        "context_window": qc_setting.context_window,
        "functions": qc_setting.mqtt_information,
    }
    return msg
