from fastapi import HTTPException
import logging
from models import TriggerSyncExtApiBase

from mqtt import publish_trigger_ext_api
from repositories.ingest import IngestRepository

logger = logging.getLogger("app.services.trigger_ext_api")


def trigger_external_api_service(
    payload: TriggerSyncExtApiBase,
    allowed_permission_group_ids: list[int],
    repo_ingest: IngestRepository,
) -> dict:
    logger.debug(
        "Trigger external API service started for ingest_ids=%s",
        payload.ingest_ids,
    )
    triggered_ids = []
    for i in set(payload.ingest_ids):
        try:
            ingest = repo_ingest.find_one(i, allowed_permission_group_ids)
        except HTTPException:
            logger.debug(
                "Skipping external API trigger for inaccessible ingest_id=%s", i
            )
            continue
        publish_trigger_ext_api(
            ingest_uuid=ingest.uuid,
            date_from=payload.start_date,
            date_to=payload.end_date,
        )
        triggered_ids.append(i)
    logger.info(
        "Triggered external API sync for %s of %s requested ingests",
        len(triggered_ids),
        len(set(payload.ingest_ids)),
    )
    return {"triggered_ingests": list(triggered_ids)}
