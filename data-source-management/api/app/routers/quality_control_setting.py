from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from access_scope import AccessScope
from dependencies import (
    get_current_user,
    get_repo_quality_control_setting,
)
from mqtt import publish_qaqc_settings_update

from models.quality_control_setting import (
    QualityControlSettingCreate,
    QualityControlSettingPublic,
    QualityControlSettingUpdate,
)
from models.filters import QualityControlSettingFilter
from models import User, QualityControlSettingRepository
from validation import QualityControlConstraints

router = APIRouter(
    prefix="/quality-control-setting",
    tags=["quality-control-setting"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)],
)

entity_name = "quality control setting"


@router.get(
    "/",
    response_model=Page[QualityControlSettingPublic],
    summary=f"Get a list of {entity_name}",
)
def read_list(
    *,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_repo_quality_control_setting),
    filters: QualityControlSettingFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_allowed_all(
            sort_by=sort_by,
            filters=filters,
            access_scope=AccessScope.from_user(current_user),
        ),
    )


@router.get(
    "/{id}",
    response_model=QualityControlSettingPublic,
    summary=f"Get one {entity_name}",
)
def read_one(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo=Depends(get_repo_quality_control_setting),
):
    return repo.find_allowed_one(id, access_scope=AccessScope.from_user(current_user))


@router.post(
    "/", response_model=QualityControlSettingPublic, summary=f"Create one {entity_name}"
)
def create(
    *,
    payload: QualityControlSettingCreate,
    current_user: User = Depends(get_current_user),
    repo: QualityControlSettingRepository = Depends(get_repo_quality_control_setting),
):
    # Validate the function arguments using the separated validation module
    is_valid, errors = QualityControlConstraints.validate_settings(
        payload.quality_control_functions
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid quality control function arguments",
                "errors": errors,
            },
        )

    extra_data = {"created_by_id": current_user.id}
    entity = repo.create_allowed(
        payload,
        extra_data,
        access_scope=AccessScope.from_user(current_user),
    )
    publish_qaqc_settings_update(entity)

    return entity


@router.patch(
    "/{id}",
    summary=f"Update one {entity_name}",
    response_model=QualityControlSettingPublic,
)
def update(
    *,
    id: int,
    payload: QualityControlSettingUpdate,
    current_user: User = Depends(get_current_user),
    repo: QualityControlSettingRepository = Depends(get_repo_quality_control_setting),
):

    if payload.quality_control_functions is not None:
        # Validate the function arguments using the separated validation module
        is_valid, errors = QualityControlConstraints.validate_settings(
            payload.quality_control_functions
        )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid quality control function arguments",
                    "errors": errors,
                },
            )

    updated = repo.update_allowed(
        id,
        payload,
        access_scope=AccessScope.from_user(current_user),
    )
    publish_qaqc_settings_update(updated)

    return updated


@router.delete("/{id}", summary=f"Delete one {entity_name}")
def delete(
    *,
    id: int,
    current_user: User = Depends(get_current_user),
    repo: QualityControlSettingRepository = Depends(get_repo_quality_control_setting),
):
    return repo.delete_allowed(id, access_scope=AccessScope.from_user(current_user))
