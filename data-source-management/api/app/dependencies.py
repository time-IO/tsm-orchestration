from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, create_engine, select
from config import settings
from auth import oidc, OIDCError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import (
    PermissionGroup,
    NeutronMonitorStation,
    User,
    BaseRepository,
    PermissionGroupRepository,
    DatabaseRepository,
    QualityControlSettingRepository,
)
import logging
from access_scope import AccessScope

from repositories.ingest import IngestRepository
from repositories.ingest_external_api import IngestExternalApiRepository
from repositories.ingest_external_api_bosch import IngestExternalApiBoschRepository
from repositories.ingest_external_api_dwd import IngestExternalApiDwdRepository
from repositories.ingest_external_api_neutron_monitor import (
    IngestExternalApiNeutronMonitorRepository,
)
from repositories.ingest_external_api_the_things_network import (
    IngestExternalApiTheThingsNetworkRepository,
)
from repositories.ingest_external_api_tsystems import (
    IngestExternalApiTSystemsRepository,
)
from repositories.ingest_external_api_uba import IngestExternalApiUbaRepository
from repositories.ingest_external_api_sensoto import IngestExternalApiSensotoRepository
from repositories.ingest_external_sftp import IngestExternalSftpRepository
from repositories.ingest_mqtt import IngestMqttRepository
from repositories.ingest_sftp import IngestSftpRepository
from repositories.parser_csv import ParserCsvRepository
from repositories.parser_json import ParserJsonRepository
from repositories.parser_detailed import ParserDetailedRepository
from repositories.parser_mqtt import ParserMqttRepository
from repositories.parser_soilcan import ParserSoilcanRepository

bearer_scheme = HTTPBearer(auto_error=False)

engine = create_engine(str(settings.DATABASE_URI))

logger = logging.getLogger("app.dependencies")


def get_session():
    with Session(engine) as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session=Depends(get_session),
) -> User:
    if not credentials:
        logger.warning("Authentication failed: missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        claims = oidc.authenticate(access_token=credentials.credentials)
    except OIDCError as exc:
        logger.warning(f"Authentication failed during OIDC validation: {str(exc)}")
        raise HTTPException(status_code=401, detail=str(exc))

    user = get_or_create_user(
        session=session,
        claims=claims,
        access_token=credentials.credentials,
    )

    if not user.is_active:
        logger.warning(f"Authentication rejected: inactive user_id={user.id}")
        raise HTTPException(status_code=403, detail="User disabled")

    return user


def get_or_create_user(*, session, claims: dict, access_token: str) -> User:
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
        logger.info(f"Created new user for subject '{external_id}'")

        return user
    except Exception as e:
        logger.error(f"Failed to get or create user: {str(e)}")
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(status_code=500, detail="Failed to get or create user")


def authenticate_token(token: str, session) -> User:
    """Authenticate a raw access token without request/header context.

    Used by the WebSocket MQTT client, where the browser cannot send an
    Authorization header, so the token arrives in the first WS message instead.
    Mirrors the validation done in ``get_current_user``.
    """
    claims = oidc.authenticate(access_token=token)
    user = get_or_create_user(session=session, claims=claims, access_token=token)
    if not user.is_active:
        raise OIDCError("User disabled")
    return user


def sync_permission_groups(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session=Depends(get_session),
    user=Depends(get_current_user),
):
    try:
        userinfo = oidc.fetch_userinfo(access_token=credentials.credentials)

        allowed_vos = settings.ALLOWED_VOS_LIST
        entitlement_array = userinfo.get("eduperson_entitlement", [])
        if isinstance(entitlement_array, str):
            entitlement_array = [entitlement_array]
        set_of_entitlements = set(entitlement_array)

        filtered_entitlements = {
            entitlement
            for entitlement in set_of_entitlements
            if PermissionGroup.get_entitlement_vo(entitlement) in allowed_vos
        }
        logger.debug(
            "Syncing permission groups for user_id=%s (entitlements total=%s, allowed=%s)",
            user.id,
            len(set_of_entitlements),
            len(filtered_entitlements),
        )

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
        logger.debug(f"Permission-group sync completed for user_id={user.id}")

    except Exception as e:
        logger.error(f"Failed to sync permission groups: {str(e)}")
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(
            status_code=500, detail=f"Failed to sync permission groups: {str(e)}"
        )


def get_repo_ingest(session=Depends(get_session)):
    return IngestRepository(session)


def get_repo_ingest_external_api(session=Depends(get_session)):
    return IngestExternalApiRepository(session)


def get_repo_ingest_external_api_uba(session=Depends(get_session)):
    return IngestExternalApiUbaRepository(session)


def get_repo_ingest_external_api_bosch(session=Depends(get_session)):
    return IngestExternalApiBoschRepository(session)


def get_repo_ingest_external_api_dwd(session=Depends(get_session)):
    return IngestExternalApiDwdRepository(session)


def get_repo_ingest_external_api_neutron_monitor(session=Depends(get_session)):
    return IngestExternalApiNeutronMonitorRepository(session)


def get_repo_ingest_external_api_sensoto(session=Depends(get_session)):
    return IngestExternalApiSensotoRepository(session)


def get_repo_ingest_external_api_the_things_network(session=Depends(get_session)):
    return IngestExternalApiTheThingsNetworkRepository(session)


def get_repo_ingest_external_api_tsystems(session=Depends(get_session)):
    return IngestExternalApiTSystemsRepository(session)


def get_repo_ingest_external_sftp(session=Depends(get_session)):
    return IngestExternalSftpRepository(session)


def get_repo_ingest_mqtt(session=Depends(get_session)):
    return IngestMqttRepository(session)


def get_repo_ingest_sftp(session=Depends(get_session)):
    return IngestSftpRepository(session)


def get_repo_parser_detailed(session=Depends(get_session)):
    return ParserDetailedRepository(session)


def get_repo_parser_csv(session=Depends(get_session)):
    return ParserCsvRepository(session)


def get_repo_parser_json(session=Depends(get_session)):
    return ParserJsonRepository(session)


def get_repo_parser_soilcan(session=Depends(get_session)):
    return ParserSoilcanRepository(session)


def get_repo_parser_mqtt(session=Depends(get_session)):
    return ParserMqttRepository(session)


def get_repo_neutron_monitor_station(session=Depends(get_session)):
    return BaseRepository(NeutronMonitorStation, session)


def get_repo_quality_control_setting(session=Depends(get_session)):
    return QualityControlSettingRepository(session)


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
        logger.debug(
            "Skipping database creation check: permission_group_id missing in request"
        )
        return

    database = database_repo.find_one_permission_group_id(permission_group_id)
    permission_group = permission_group_repo.find_one(permission_group_id)

    if not permission_group:
        logger.error("Cannot create database entity: permission group does not exist")
        return

    if not database:
        logger.debug(
            f"Creating database entity for permission_group_id={permission_group_id}"
        )
        database_repo.create(
            permission_group, access_scope=AccessScope.from_user(current_user)
        )
