from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine
from .routers import projects, ingest_s3stores, ingest_mqtt, csv_parser, ingest_external_api_the_things_network, \
    ingest_external_sftp, ingest_external_api_tsystems, ingest_external_api_uba, ingest_external_api_dwd, \
    ingest_external_api_neutron_monitor, ingest_external_api_bosch, quality_control_setting, neutron_monitor_stations, health
from fastapi.middleware.cors import CORSMiddleware

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

origins = [
    "http://localhost",
    "http://localhost:3000",
]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# the order of the router defines the order of the openapi doc
app.include_router(csv_parser.router)
app.include_router(ingest_external_api_bosch.router)
app.include_router(ingest_external_api_dwd.router)
app.include_router(ingest_external_api_neutron_monitor.router)
app.include_router(ingest_external_api_the_things_network.router)
app.include_router(ingest_external_api_tsystems.router)
app.include_router(ingest_external_api_uba.router)
app.include_router(ingest_external_sftp.router)
app.include_router(ingest_mqtt.router)
app.include_router(ingest_s3stores.router)
app.include_router(neutron_monitor_stations.router)
app.include_router(projects.router)
app.include_router(quality_control_setting.router)
app.include_router(health.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

