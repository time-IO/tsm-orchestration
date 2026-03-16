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
