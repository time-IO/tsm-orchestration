from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination import paginate
from dependencies import (
    get_session,
    get_current_user,
    get_repo_quality_control_setting,
)
from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError

from models.quality_control_setting import (
    QualityControlSettingCreate,
    QualityControlSetting,
    QualityControlFunction,
    QualityControlFunctionArgument,
    QualityControlSettingPublic,
)
from models.filters import QualityControlSettingFilter

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
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_quality_control_setting),
    filters: QualityControlSettingFilter = Depends(),
    sort_by: str | None = None,
):
    return paginate(
        repo.find_allowed_all(
            current_user.permission_group_ids, sort_by, filters=filters
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
    current_user=Depends(get_current_user),
    repo=Depends(get_repo_quality_control_setting),
):
    return repo.find_allowed_one(id, current_user.permission_group_ids)


@router.post(
    "/", response_model=QualityControlSettingPublic, summary=f"Create one {entity_name}"
)
def create(
    *,
    session: Session = Depends(get_session),
    payload: QualityControlSettingCreate,
    user=Depends(get_current_user),
):

    try:

        existing_statement = select(QualityControlSetting).where(
            func.lower(QualityControlSetting.name) == func.lower(str(payload.name)),
            QualityControlSetting.permission_group_id == payload.permission_group_id,
        )
        existing = session.exec(existing_statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="This name already exists.")

        extra_data = {"created_by_id": user.id}

        data = payload.model_dump(exclude={"quality_control_functions"})
        entity = QualityControlSetting.model_validate(data, update=extra_data)

        session.add(entity)
        session.flush()

        quality_control_setting_id_data = {"quality_control_setting_id": entity.id}

        for function_payload in payload.quality_control_functions:

            function_data = function_payload.model_dump(
                exclude={"quality_control_function_arguments"}
            )
            db_function = QualityControlFunction.model_validate(
                function_data, update=quality_control_setting_id_data
            )

            session.add(db_function)
            session.flush()

            quality_control_function_id_data = {
                "quality_control_function_id": db_function.id
            }

            for (
                function_argument_payload
            ) in function_payload.quality_control_function_arguments:
                db_argument = QualityControlFunctionArgument.model_validate(
                    function_argument_payload, update=quality_control_function_id_data
                )
                session.add(db_argument)

        session.commit()
        session.refresh(entity)

        return entity
    except HTTPException as exc:
        raise exc
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{entity_name} with the same name and permission group already exists.",
        )
    except:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create {entity_name}")
