import logging
from fastapi import HTTPException
from models import (
    BaseRepository,
    TriggerQualityControl,
)
from mqtt import publish_trigger_quality_control

logger = logging.getLogger("app.services.trigger_quality_control")


def trigger_quality_control_service(
    payload: TriggerQualityControl,
    allowed_permission_group_ids: list[int],
    repo_quality_control: BaseRepository,
) -> dict:

    triggered_ids = []
    for identifier in set(payload.quality_control_setting_ids):
        try:
            qc_setting = repo_quality_control.find_allowed_one(
                identifier, allowed_permission_group_ids
            )
        except HTTPException:
            continue
        publish_trigger_quality_control(
            database_uuid=str(qc_setting.permission_group.uuid),
            qc_settings_name=qc_setting.name,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        triggered_ids.append(identifier)

    return {"triggered_quality_control_settings": list(triggered_ids)}
