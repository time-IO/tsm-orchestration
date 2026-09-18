import os
import logging

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import disable_installed_extensions_check
from routers import (
    permission_group,
    ingest_sftp,
    ingest_sftp_storage,
    ingest_external_sftp_storage,
    ingest_mqtt,
    ingest_mqtt_client,
    parser_csv,
    parser_json,
    ingest_external_api_the_things_network,
    ingest_external_sftp,
    ingest_external_api_tsystems,
    ingest_external_api_uba,
    ingest_external_api_dwd,
    ingest_external_api_neutron_monitor,
    ingest_external_api_bosch,
    ingest_external_api_sensoto,
    quality_control_setting,
    neutron_monitor_station,
    health,
    parser_mqtt,
    user,
    sta_proxy,
    trigger_quality_control,
    trigger_ext_api,
    trigger_ext_sftp,
    parser_timezone,
    parser_encoding,
    ingest,
    parser_detailed,
    usage_statistics,
    ingest_external_api,
    parser_soilcan,
)
from fastapi.middleware.cors import CORSMiddleware
from config import settings

API_ROOT_PATH = os.environ.get("API_ROOT_PATH", "/api")
app = FastAPI(root_path=API_ROOT_PATH)
add_pagination(app)
disable_installed_extensions_check()

log_level = os.environ.get("LOG_LEVEL", "info").upper()
if log_level == "TRACE":
    log_level = "DEBUG"
logging.getLogger().setLevel(log_level)
logging.getLogger("app").setLevel(log_level)
logging.getLogger("app.main").info(
    "API startup configured with LOG_LEVEL=%s and API_ROOT_PATH=%s",
    log_level,
    API_ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# the order of the router defines the order of the openapi doc
app.include_router(parser_csv.router)
app.include_router(parser_json.router)
app.include_router(parser_soilcan.router)
app.include_router(ingest.router)
app.include_router(ingest_external_api_bosch.router)
app.include_router(ingest_external_api_dwd.router)
app.include_router(ingest_external_api_neutron_monitor.router)
app.include_router(ingest_external_api_the_things_network.router)
app.include_router(ingest_external_api_tsystems.router)
app.include_router(ingest_external_api_uba.router)
app.include_router(ingest_external_api_sensoto.router)
app.include_router(ingest_external_sftp.router)
app.include_router(ingest_mqtt.router)
app.include_router(ingest_mqtt_client.router)
app.include_router(ingest_sftp.router)
app.include_router(ingest_sftp_storage.router)
app.include_router(ingest_external_sftp_storage.router)
app.include_router(parser_mqtt.router)
app.include_router(neutron_monitor_station.router)
app.include_router(permission_group.router)
app.include_router(quality_control_setting.router)
app.include_router(health.router)
app.include_router(user.router)
app.include_router(sta_proxy.router)
app.include_router(trigger_quality_control.router)
app.include_router(trigger_ext_api.router)
app.include_router(trigger_ext_sftp.router)
app.include_router(parser_timezone.router)
app.include_router(parser_encoding.router)
app.include_router(parser_detailed.router)
app.include_router(usage_statistics.router)
app.include_router(ingest_external_api.router)
