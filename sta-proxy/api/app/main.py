import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import frost_endpoints, frost_proxy
from services import close_frost_client
from config import settings

API_ROOT_PATH = os.environ.get("API_ROOT_PATH", "/api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_frost_client()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(frost_endpoints.router)
app.include_router(frost_proxy.router)