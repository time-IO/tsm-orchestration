import logging

from fastapi import HTTPException

from access_scope import AccessScope
from constants import REPARSABLE_INGEST_TYPES
from models import TriggerReparseBase
from mqtt import publish_trigger_reparse
from repositories.ingest import IngestRepository
from repositories.parser_detailed import ParserDetailedRepository

logger = logging.getLogger("app.services.trigger_reparse")


def _timezone_of(parser) -> str | None:
    """Timezone setting of a parser, None if it has none (e.g. soilcan)."""
    if parser.parser_csv is not None:
        return parser.parser_csv.timezone
    if parser.parser_json is not None:
        return parser.parser_json.timezone
    return None


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
    warnings: list[str] = []
    if payload.parser_id is not None:
        parser = repo_parser.find_one(payload.parser_id, access_scope=access_scope)
        parser_uuid = str(parser.parser.uuid)

        if (
            payload.include_parsed
            and ingest.parser_id is not None
            and ingest.parser_id != payload.parser_id
        ):
            current = repo_parser.find_one(ingest.parser_id, access_scope=access_scope)
            new_tz, current_tz = _timezone_of(parser), _timezone_of(current)
            if new_tz and current_tz and new_tz != current_tz:
                warnings.append(
                    f"The timezone of the selected parser ({new_tz}) differs from "
                    f"the current parser of this ingest ({current_tz}). Already "
                    "parsed files that were parsed with a different timezone will "
                    "probably not be reparsed. Please check the journal."
                )

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
    return {"triggered_ingest": payload.ingest_id, "warnings": warnings}
