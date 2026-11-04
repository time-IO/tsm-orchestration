import logging

from fastapi import HTTPException

from access_scope import AccessScope
from constants import REPARSABLE_INGEST_TYPES
from models import TriggerReparseBase
from mqtt import publish_trigger_reparse
from repositories.ingest import IngestRepository
from repositories.parser_detailed import ParserDetailedRepository

logger = logging.getLogger("app.services.trigger_reparse")


def trigger_reparse_service(
    payload: TriggerReparseBase,
    repo_ingest: IngestRepository,
    repo_parser: ParserDetailedRepository,
    access_scope: AccessScope,
) -> dict:
    ingest = repo_ingest.find_one(payload.ingest_id, access_scope=access_scope)

    if not access_scope.can_reparse(ingest.permission_group_id):
        raise HTTPException(
            status_code=403, detail="Not allowed to reparse files of this ingest."
        )
    if ingest.ingest_type not in REPARSABLE_INGEST_TYPES:
        raise HTTPException(status_code=422, detail="Ingest type not supported.")

    parser_uuid = None
    if payload.parser_id is not None:
        parser = repo_parser.find_one(payload.parser_id, access_scope=access_scope)
        parser_uuid = str(parser.parser.uuid)

    publish_trigger_reparse(
        ingest_uuid=ingest.uuid,
        start_date=payload.start_date,
        end_date=payload.end_date,
        filename_pattern=payload.filename_pattern,
        parser_uuid=parser_uuid,
        include_parsed=payload.include_parsed,
        parsed_files_parser=payload.parsed_files_parser,
    )
    logger.info("Triggered reparse for ingest_id=%s", payload.ingest_id)
    return {"triggered_ingest": payload.ingest_id}
