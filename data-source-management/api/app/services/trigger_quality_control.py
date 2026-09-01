import logging
from access_scope import AccessScope
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
    access_scope: AccessScope | None = None,
) -> dict:
    if access_scope is None:
        access_scope = AccessScope(allowed_permission_group_ids)

    logger.debug(
        "Trigger quality-control service started for ids=%s",
        payload.quality_control_setting_ids,
    )
    triggered_ids = []
    for identifier in set(payload.quality_control_setting_ids):
        try:
            qc_setting = repo_quality_control.find_allowed_one(
                identifier, access_scope=access_scope
            )
        except HTTPException:
            logger.debug(
                "Skipping quality-control trigger for inaccessible setting_id=%s",
                identifier,
            )
            continue
        publish_trigger_quality_control(
            permission_group_uuid=str(qc_setting.permission_group.uuid),
            qc_settings_name=qc_setting.name,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        triggered_ids.append(identifier)
    logger.info(
        "Triggered quality-control for %s of %s requested settings",
        len(triggered_ids),
        len(set(payload.quality_control_setting_ids)),
    )

    return {"triggered_quality_control_settings": list(triggered_ids)}
