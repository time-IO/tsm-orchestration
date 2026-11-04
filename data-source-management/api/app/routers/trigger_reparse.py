import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from access_scope import AccessScope
from dependencies import get_current_user, get_repo_ingest, get_repo_parser_detailed
from models import TriggerReparseBase, TriggerReparseResponse, User
from services import trigger_reparse_service

logger = logging.getLogger("app.routers.trigger_reparse")

CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/trigger/reparse",
    tags=["trigger/reparse"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=TriggerReparseResponse,
    summary="Triggers a MQTT message to reparse files of a file-based ingest",
)
def trigger_reparse(
    current_user: CurrentUser,
    payload: TriggerReparseBase,
    repo_ingest=Depends(get_repo_ingest),
    repo_parser=Depends(get_repo_parser_detailed),
):
    logger.debug(
        "Trigger reparse requested by user_id=%s for ingest_id=%s, range=%s..%s",
        current_user.id,
        payload.ingest_id,
        payload.start_date,
        payload.end_date,
    )
    return trigger_reparse_service(
        payload=payload,
        repo_ingest=repo_ingest,
        repo_parser=repo_parser,
        access_scope=AccessScope.from_user(current_user),
    )
