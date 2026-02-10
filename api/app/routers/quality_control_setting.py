from fastapi import APIRouter, Depends
from ..dependencies import get_session, get_current_user
from sqlmodel import Session, select

from ..models.quality_control_setting import QualityControlSettingCreate, QualityControlSetting, QualityControlFunction, \
    QualityControlFunctionArgument, QualityControlSettingPublic

router = APIRouter(
    prefix="/quality-control-setting",
    tags=["quality-control-setting"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

entity_name = "quality control setting"


@router.get("/", response_model=list[QualityControlSettingPublic], summary=f"Get a list of {entity_name}")
def read_list(
        *,
        session: Session = Depends(get_session)
):
    entities = session.exec(select(QualityControlSetting)).all()
    return entities


@router.post("/", response_model=QualityControlSettingPublic, summary=f"Create one {entity_name}")
def create(*, session: Session = Depends(get_session), payload: QualityControlSettingCreate, user=Depends(get_current_user)):

    extra_data = {"created_by_id": user.id}

    data = payload.model_dump(exclude={"quality_control_functions"})
    entity = QualityControlSetting.model_validate(data, update=extra_data)

    session.add(entity)
    session.flush()

    quality_control_setting_id_data = {"quality_control_setting_id": entity.id}

    for function_payload in payload.quality_control_functions:

        function_data = function_payload.model_dump(exclude={"quality_control_function_arguments"})
        db_function = QualityControlFunction.model_validate(function_data, update=quality_control_setting_id_data)

        session.add(db_function)
        session.flush()

        quality_control_function_id_data = {"quality_control_function_id": db_function.id}

        for function_argument_payload in function_payload.quality_control_function_arguments:
            db_argument = QualityControlFunctionArgument.model_validate(function_argument_payload,
                                                                        update=quality_control_function_id_data)
            session.add(db_argument)

    session.commit()
    session.refresh(entity)

    return entity
