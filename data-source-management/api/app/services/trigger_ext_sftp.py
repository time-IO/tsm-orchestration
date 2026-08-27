import logging
from access_scope import AccessScope
from models import TriggerSyncExtSftpBase

from mqtt import publish_trigger_ext_sftp
from repositories.ingest import IngestRepository

logger = logging.getLogger("app.services.trigger_ext_sftp")


def trigger_external_sftp_service(
    payload: TriggerSyncExtSftpBase,
    allowed_permission_group_ids: list[int],
    repo_ingest: IngestRepository,
    access_scope: AccessScope | None = None,
) -> dict:
    if access_scope is None:
        access_scope = AccessScope(allowed_permission_group_ids)

    logger.debug(
        "Trigger external SFTP service started for ingest_id=%s range=%s..%s",
        payload.ingest_id,
        payload.start_date,
        payload.end_date,
    )
    ingest = repo_ingest.find_one(payload.ingest_id, access_scope=access_scope)
    publish_trigger_ext_sftp(
        ingest_uuid=ingest.uuid,
        datetime_from=payload.start_date,
        datetime_to=payload.end_date,
    )
    logger.info("Triggered external SFTP sync for ingest_id=%s", payload.ingest_id)
    return {"triggered_ingest": payload.ingest_id}
