from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, create_engine, select
from config import settings
from auth import oidc, OIDCError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import (
    PermissionGroup,
    IngestExternalApiBosch,
    IngestExternalApiDwd,
    IngestExternalApiNeutronMonitor,
    IngestExternalApiTheThingsNetwork,
    IngestExternalApiTSystems,
    IngestExternalApiUba,
    IngestExternalSftp,
    IngestMqtt,
    IngestS3Store,
    MqttParser,
    NeutronMonitorStation,
    CsvParser,
    QualityControlSetting,
    User,
    BaseRepository,
    PermissionGroupRepository,
    DatabaseRepository,
)
import logging

bearer_scheme = HTTPBearer(auto_error=False)

engine = create_engine(str(settings.DATABASE_URI))

logger = logging.getLogger("app.dependencies")


def get_session():
    with Session(engine) as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session=Depends(get_session),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        claims = oidc.authenticate(access_token=credentials.credentials)
    except OIDCError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    user = get_or_create_user(
        session=session,
        claims=claims,
        access_token=credentials.credentials,
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")

    return user


def get_or_create_user(*, session, claims: dict, access_token: str):
    try:
        external_id = claims["sub"]

        stmt = select(User).where(User.sub == external_id)
        user = session.exec(stmt).first()

        if user:
            return user

        userinfo = oidc.fetch_userinfo(access_token)

        if userinfo.get("sub") != external_id:
            raise OIDCError("Userinfo subject mismatch")

        user = User(
            sub=external_id,
            email=userinfo.get("email"),
            given_name=userinfo.get("given_name"),
            family_name=userinfo.get("family_name"),
            username=userinfo.get("eduperson_principal_name"),
            is_active=True,
            is_superuser=False,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user
    except Exception as e:
        logger.error(f"Failed to get or create user: {str(e)}")
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(status_code=500, detail="Failed to get or create user")


def sync_permission_groups(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    try:
        userinfo = oidc.fetch_userinfo(access_token=credentials.credentials)

        allowed_vos = settings.ALLOWED_VOS_LIST
        set_of_entitlements = set(userinfo.get("eduperson_entitlement", []))

        filtered_entitlements = {
            entitlement
            for entitlement in set_of_entitlements
            if PermissionGroup.get_entitlement_vo(entitlement) in allowed_vos
        }

        existing_permission_groups = user.permission_groups

        # Remove groups the user no longer belongs to
        for current_permission_group in existing_permission_groups:
            entitlement = current_permission_group.entitlement
            if entitlement and entitlement not in filtered_entitlements:
                user.permission_groups.remove(current_permission_group)
                session.add(current_permission_group)

        # Add new/missing groups
        for entitlement in filtered_entitlements:
            permission_group = (
                session.query(PermissionGroup)
                .filter_by(entitlement=entitlement)
                .first()
            )
            if not permission_group:
                name = PermissionGroup.convert_entitlement_to_name(entitlement)
                permission_group = PermissionGroup(entitlement=entitlement, name=name)
                session.add(permission_group)
            if permission_group not in user.permission_groups:
                user.permission_groups.append(permission_group)

        # Commit once at the end
        session.commit()

    except Exception as e:
        logger.error(f"Failed to sync permission groups: {str(e)}")
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(
            status_code=500, detail=f"Failed to sync permission groups: {str(e)}"
        )


def get_repo_ingest_external_api_uba(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiUba, session)


def get_repo_ingest_external_api_bosch(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiBosch, session)


def get_repo_ingest_external_api_dwd(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiDwd, session)


def get_repo_ingest_external_api_neutron_monitor(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiNeutronMonitor, session)


def get_repo_ingest_external_api_the_things_network(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiTheThingsNetwork, session)


def get_repo_ingest_external_api_tsystems(session=Depends(get_session)):
    return BaseRepository(IngestExternalApiTSystems, session)


def get_repo_ingest_external_sftp(session=Depends(get_session)):
    return BaseRepository(IngestExternalSftp, session)


def get_repo_ingest_mqtt(session=Depends(get_session)):
    return BaseRepository(IngestMqtt, session)


def get_repo_ingest_s3stores(session=Depends(get_session)):
    return BaseRepository(IngestS3Store, session)


def get_repo_csv_parser(session=Depends(get_session)):
    return BaseRepository(CsvParser, session)


def get_repo_mqtt_parser(session=Depends(get_session)):
    return BaseRepository(MqttParser, session)


def get_repo_neutron_monitor_station(session=Depends(get_session)):
    return BaseRepository(NeutronMonitorStation, session)


def get_repo_quality_control_setting(session=Depends(get_session)):
    return BaseRepository(QualityControlSetting, session)


def get_repo_csv_parser_timestamp_column(session=Depends(get_session)):
    return BaseRepository(CsvParser, session)


def get_repo_database(session=Depends(get_session)):
    return DatabaseRepository(session)


def get_repo_permission_group(session=Depends(get_session)):
    return PermissionGroupRepository(session)


async def create_database_if_not_exists(
    request: Request,
    database_repo=Depends(get_repo_database),
    permission_group_repo=Depends(get_repo_permission_group),
    current_user=Depends(get_current_user),
):
    body = await request.json()
    permission_group_id = body.get("permission_group_id")

    if not permission_group_id:
        # this method will also be called for update routes
        # we currently use http.patch so the body may not include permisison_group_id so we skip here
        return

    database = database_repo.find_one_permission_group_id(permission_group_id)
    permission_group = permission_group_repo.find_one(permission_group_id)

    if not permission_group:
        logger.error("Cannot create database entity: permission group does not exist")
        return

    if not database:
        database_repo.create(permission_group, current_user.permission_group_ids)
