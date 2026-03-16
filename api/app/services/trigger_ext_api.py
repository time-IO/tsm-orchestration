from fastapi import HTTPException
from models import TriggerSyncExtApiBase, BaseRepository

from mqtt import publish_trigger_ext_api


def trigger_external_api_service(
    payload: TriggerSyncExtApiBase,
    allowed_permission_group_ids: list[int],
    repo_ingest: BaseRepository,
) -> dict:
    triggered_ids = []
    for i in set(payload.ingest_ids):
        try:
            ingest = repo_ingest.find_allowed_one(i, allowed_permission_group_ids)
        except HTTPException:
            continue
        publish_trigger_ext_api(
            ingest_uuid=ingest.uuid,
            date_from=payload.start_date,
            date_to=payload.end_date,
        )
        triggered_ids.append(i)
    return {"triggered_ingests": list(triggered_ids)}
