from fastapi import APIRouter, Depends
from access_scope import AccessScope
from typing import Any
from models import TriggerQualityControl, User
from dependencies import (
    get_current_user,
    get_repo_quality_control_setting,
)
import logging
from services import trigger_quality_control_service
from typing import Annotated

logger = logging.getLogger("app.routers.trigger_quality_control")

CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/trigger/quality_control",
    tags=["trigger/quality_control"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)


@router.post("/", summary="Trigger quality control")
def trigger_quality_control(
    payload: TriggerQualityControl,
    current_user: CurrentUser,
    repo_quality_control=Depends(get_repo_quality_control_setting),
) -> Any:
    logger.debug(
        "Trigger quality-control requested by user_id=%s for ids=%s range=%s..%s",
        current_user.id,
        payload.quality_control_setting_ids,
        payload.start_date,
        payload.end_date,
    )
    return trigger_quality_control_service(
        payload=payload,
        allowed_permission_group_ids=current_user.permission_group_ids,
        repo_quality_control=repo_quality_control,
        access_scope=AccessScope.from_user(current_user),
    )
