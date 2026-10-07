import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routers import frost_endpoints, frost_proxy, ingests, user
from services import close_dsm_client, close_frost_client
from config import settings

API_ROOT_PATH = os.environ.get("API_ROOT_PATH", "/api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_frost_client()
    await close_dsm_client()


app = FastAPI(
    root_path=API_ROOT_PATH,
    lifespan=lifespan,
)

log_level = os.environ.get("LOG_LEVEL", "info").upper()
if log_level == "TRACE":
    log_level = "DEBUG"
logging.getLogger().setLevel(log_level)
logging.getLogger("app").setLevel(log_level)
logging.getLogger("app.main").info(
    "API startup configured with LOG_LEVEL=%s, API_ROOT_PATH=%s and FROST_URL=%s",
    log_level,
    API_ROOT_PATH,
    settings.FROST_URL,
)

app.include_router(frost_endpoints.router)
app.include_router(ingests.router)
app.include_router(user.router)
app.include_router(frost_proxy.router)
