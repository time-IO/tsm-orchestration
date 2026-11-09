from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_ingest,
    get_superuser,
)
from models import (
    CustomJob,
    CustomJobCreate,
    CustomJobRead,
    CustomJobSpec,
    CustomJobUpdate,
    IngestScheduleInfoRead,
    User,
)
from models.filters import IngestFilter
from models.ingest import IngestWithApiInfoRead
from repositories.ingest import IngestRepository
from services import custom_jobs
from services.ingest_schedule import build_custom_job_read, build_schedule_info
from services.db_api import get_ingest_configurations, get_ingest_journal
import logging

from fastapi_pagination import Page
from fastapi_pagination import paginate

logger = logging.getLogger("app.routers.ingest")

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "ingest"


@router.get(
    "/",
    response_model=Page[IngestWithApiInfoRead],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest),
    filters: IngestFilter = Depends(),
    sort_by: str | None = None,
):
    logger.debug(
        "List ingest requested by user_id=%s sort_by=%s filters=%s",
        current_user.id,
        sort_by,
        filters,
    )
    return paginate(
        repo.find_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        )
    )


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: IngestRepository = Depends(get_repo_ingest),
):
    logger.debug(
        "Delete ingest requested by user_id=%s ingest_id=%s", current_user.id, id
    )
    return repo.delete(id, access_scope=AccessScope.from_user(current_user))


@router.get("/{ingest_id}/configurations", tags=["ingest/configurations"])
async def read_ingest_configurations(
    ingest_id: int,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    return await get_ingest_configurations(ingest.uuid)


@router.get("/{ingest_id}/journal", tags=["ingest/journal"])
async def read_ingest_journal(
    ingest_id: int,
    datetime_from: Optional[str] = Query(None),
    datetime_to: Optional[str] = Query(None),
    level: Optional[str] = Query(
        None, description="Filter by level, e.g. INFO/WARNING/ERROR"
    ),
    limit: int = Query(100, description="Max entries, newest first"),
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    return await get_ingest_journal(
        ingest.uuid,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        level=level,
        limit=limit,
    )


@router.get(
    "/{ingest_id}/schedule",
    response_model=IngestScheduleInfoRead,
    tags=["ingest/schedule"],
    summary="Get the sync schedule and manual cron jobs of one ingest",
)
def read_ingest_schedule(
    ingest_id: int,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    return build_schedule_info(
        repo.find_schedule(ingest), repo.find_custom_jobs(ingest)
    )


custom_job_tags = ["ingest/custom-jobs"]


@router.get(
    "/{ingest_id}/custom-jobs/available",
    response_model=list[CustomJobSpec],
    tags=custom_job_tags,
    summary="Get the custom job types that can be defined for one ingest",
)
def read_available_custom_jobs(
    ingest_id: int,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_superuser),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    return custom_jobs.available_jobs(ingest.ingest_type)


@router.post(
    "/{ingest_id}/custom-jobs",
    response_model=CustomJobRead,
    status_code=201,
    tags=custom_job_tags,
    summary="Create a custom job for one ingest (superuser only)",
)
def create_custom_job(
    ingest_id: int,
    payload: CustomJobCreate,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_superuser),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    definition = custom_jobs.validate_job_type(payload.job_type, ingest.ingest_type)
    job = repo.save_custom_job(
        CustomJob(
            job_type=payload.job_type.value,
            ingest_id=ingest.id,
            params=custom_jobs.validate_params(definition, payload.params),
            cron_expression=custom_jobs.normalize_cron_expression(
                payload.cron_expression
            ),
            jitter_seconds=(
                custom_jobs.random_jitter()
                if payload.jitter_seconds is None
                else payload.jitter_seconds
            ),
            enabled=payload.enabled,
            note=payload.note,
        )
    )
    logger.info(
        "Custom job %s (%s) created for ingest_id=%s by user_id=%s",
        job.id,
        job.job_type,
        ingest.id,
        current_user.id,
    )
    return build_custom_job_read(job)


@router.patch(
    "/{ingest_id}/custom-jobs/{job_id}",
    response_model=CustomJobRead,
    tags=custom_job_tags,
    summary="Update a custom job of one ingest (superuser only)",
)
def update_custom_job(
    ingest_id: int,
    job_id: int,
    payload: CustomJobUpdate,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_superuser),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    job = repo.find_custom_job(ingest, job_id)
    # only the note may be cleared
    data = {
        k: v
        for k, v in payload.model_dump(exclude_unset=True).items()
        if v is not None or k == "note"
    }
    if "cron_expression" in data:
        data["cron_expression"] = custom_jobs.normalize_cron_expression(
            data["cron_expression"]
        )
    if "params" in data:
        definition = custom_jobs.CATALOG[job.job_type]
        data["params"] = custom_jobs.validate_params(definition, data["params"])
    job.sqlmodel_update(data)
    job = repo.save_custom_job(job)
    logger.info(
        "Custom job %s updated for ingest_id=%s by user_id=%s",
        job.id,
        ingest.id,
        current_user.id,
    )
    return build_custom_job_read(job)


@router.delete(
    "/{ingest_id}/custom-jobs/{job_id}",
    status_code=204,
    tags=custom_job_tags,
    summary="Delete a custom job of one ingest (superuser only)",
)
def delete_custom_job(
    ingest_id: int,
    job_id: int,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_superuser),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    repo.delete_custom_job(repo.find_custom_job(ingest, job_id))
    logger.info(
        "Custom job %s deleted for ingest_id=%s by user_id=%s",
        job_id,
        ingest.id,
        current_user.id,
    )


@router.get("/{ingest_id}/database", tags=["ingest/database"])
async def read_ingest_database_name(
    ingest_id: int,
    repo: IngestRepository = Depends(get_repo_ingest),
    current_user: User = Depends(get_current_user),
):
    ingest = repo.find_one(ingest_id, access_scope=AccessScope.from_user(current_user))
    database = ingest.permission_group.database
    if database is None:
        raise HTTPException(status_code=404, detail="No database for this ingest")
    return database.username
