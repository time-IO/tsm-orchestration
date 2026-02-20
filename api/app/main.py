import os

from fastapi import FastAPI
from sqlmodel import SQLModel
from .routers import (
    permission_group,
    ingest_s3store,
    ingest_mqtt,
    parser_csv,
    ingest_external_api_the_things_network,
    ingest_external_sftp,
    ingest_external_api_tsystems,
    ingest_external_api_uba,
    ingest_external_api_dwd,
    ingest_external_api_neutron_monitor,
    ingest_external_api_bosch,
    quality_control_setting,
    neutron_monitor_station,
    health,
    parser_mqtt,
    user,
)
from fastapi.middleware.cors import CORSMiddleware
from .dependencies import engine
from .config import settings


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


API_ROOT_PATH = os.environ.get("API_ROOT_PATH", "/api")
app = FastAPI(root_path=API_ROOT_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# the order of the router defines the order of the openapi doc
app.include_router(parser_csv.router)
app.include_router(ingest_external_api_bosch.router)
app.include_router(ingest_external_api_dwd.router)
app.include_router(ingest_external_api_neutron_monitor.router)
app.include_router(ingest_external_api_the_things_network.router)
app.include_router(ingest_external_api_tsystems.router)
app.include_router(ingest_external_api_uba.router)
app.include_router(ingest_external_sftp.router)
app.include_router(ingest_mqtt.router)
app.include_router(ingest_s3store.router)
app.include_router(parser_mqtt.router)
app.include_router(neutron_monitor_station.router)
app.include_router(permission_group.router)
app.include_router(quality_control_setting.router)
app.include_router(health.router)
app.include_router(user.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
