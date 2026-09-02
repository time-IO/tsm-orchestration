from fastapi import APIRouter, Depends
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest_external_api_bosch,
    get_repo_ingest_external_api_tsystems,
    get_repo_ingest_external_api_dwd,
    get_repo_ingest_external_api_uba,
    get_repo_ingest_external_api_the_things_network,
    get_repo_ingest_external_api_neutron_monitor,
    get_repo_ingest,
)
from models import TriggerSyncExtApiBase, TriggerSyncExtApiResponse, User
import logging
from typing import Annotated
from services import trigger_external_api_service

logger = logging.getLogger("app.routers.trigger_extapi")

CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(
    prefix="/trigger/external-api",
    tags=["trigger/external-api"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=TriggerSyncExtApiResponse,
    summary=f"Triggers a MQTT message to sync historic data of at least one external api ingest",
)
def trigger_api(
    current_user: CurrentUser,
    payload: TriggerSyncExtApiBase,
    repo=Depends(get_repo_ingest),
):
    logger.debug(
        "Trigger external API sync requested by user_id=%s for ingest_ids=%s range=%s..%s",
        current_user.id,
        payload.ingest_ids,
        payload.start_date,
        payload.end_date,
    )
    return trigger_external_api_service(
        payload=payload,
        allowed_permission_group_ids=current_user.permission_group_ids,
        repo_ingest=repo,
        access_scope=AccessScope.from_user(current_user),
    )


#
#
# @router.post(
#     "/bosch",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one bosch_api ingest",
# )
# def trigger_bosch_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_bosch),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
#
#
# @router.post(
#     "/tsystems",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one tsystems_api ingest",
# )
# def trigger_tsystems_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_tsystems),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
#
#
# @router.post(
#     "/dwd",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one dwd_api ingest",
# )
# def trigger_dwd_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_dwd),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
#
#
# @router.post(
#     "/uba",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one uba_api ingest",
# )
# def trigger_uba_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_uba),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
#
#
# @router.post(
#     "/the-things-network",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one ttn_api ingest",
# )
# def trigger_ttn_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_the_things_network),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
#
#
# @router.post(
#     "/neutron-monitor",
#     response_model=TriggerSyncExtApiResponse,
#     summary=f"Triggers a MQTT message to sync historic data of at least one nm_api ingest",
# )
# def trigger_nm_api(
#         current_user: CurrentUser,
#         payload: TriggerSyncExtApiBase,
#         repo=Depends(get_repo_ingest_external_api_neutron_monitor),
# ):
#     return trigger_external_api_service(
#         payload=payload,
#         allowed_permission_group_ids=current_user.permission_group_ids,
#         repo_ingest=repo,
#     )
