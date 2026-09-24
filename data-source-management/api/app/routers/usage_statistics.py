from fastapi import APIRouter, Depends

from dependencies import get_session
from models import (
    PermissionGroup,
    User,
    IngestExternalApiBosch,
    IngestExternalApiDwd,
    IngestExternalApiNeutronMonitor,
    IngestExternalApiTheThingsNetwork,
    IngestExternalApiTSystems,
    IngestExternalApiUba,
    IngestExternalSftp,
    IngestMqtt,
    IngestSftp,
    QualityControlSetting,
    ParserCsv,
    Ingest,
)

router = APIRouter(
    prefix="/usage-statistics",
    tags=["usage-statistics"],
    responses={404: {"description": "Not found"}},
)


# this route does currently not require authentication
@router.get("/", summary=f"Get usage statistics")
def read_list(*, session=Depends(get_session)):
    models_to_query = {
        "projects": PermissionGroup,
        "users": User,
        "ingest_external_api_bosch": IngestExternalApiBosch,
        "ingest_external_api_dwd": IngestExternalApiDwd,
        "ingest_external_api_neutronmonitor": IngestExternalApiNeutronMonitor,
        "ingest_external_api_thethingsnetwork": IngestExternalApiTheThingsNetwork,
        "ingest_external_api_tsystems": IngestExternalApiTSystems,
        "ingest_external_api_uba": IngestExternalApiUba,
        "ingest_external_sftp": IngestExternalSftp,
        "ingest_mqtt": IngestMqtt,
        "ingest_s3store": IngestSftp,
        "quality_control_setting": QualityControlSetting,
        "parser_csv": ParserCsv,
        "ingests": Ingest,
    }
    counts = {}
    for model_name, model in models_to_query.items():
        count = session.query(model).count()
        counts[model_name] = count

    return {"counts": counts}
