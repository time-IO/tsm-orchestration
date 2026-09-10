from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_sftp,
)
from models import TriggerSyncExtSftpBase, TriggerSyncExtSftpResponse, User
import logging
from typing import Annotated
from services import trigger_external_sftp_service

logger = logging.getLogger("app.routers.trigger_extsftp")

CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/trigger/external-sftp",
    tags=["trigger/external-sftp"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=TriggerSyncExtSftpResponse,
    summary="Triggers a MQTT message to (re)sync an external sftp ingest",
)
def trigger_sftp(
    current_user: CurrentUser,
    payload: TriggerSyncExtSftpBase,
    repo=Depends(get_repo_ingest_external_sftp),
):
    logger.debug(
        "Trigger external SFTP sync requested by user_id=%s for ingest_id=%s range=%s..%s",
        current_user.id,
        payload.ingest_id,
        payload.start_date,
        payload.end_date,
    )
    return trigger_external_sftp_service(
        payload=payload,
        repo_ext_sftp=repo,
        access_scope=AccessScope.from_user(current_user),
    )
