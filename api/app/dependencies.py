from fastapi import Depends, HTTPException
from sqlmodel import Session, create_engine, select
from .config import settings
from .auth import oidc, OIDCError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models.user import User
from .models.permission_group import PermissionGroup

bearer_scheme = HTTPBearer(auto_error=False)

engine = create_engine(str(settings.DATABASE_URI))


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
    except:
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(
            status_code=500, detail="Failed to get or create user"
        )


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
        session.rollback()
        # Optionally log or re-raise, depending on your error handling strategy
        raise HTTPException(
            status_code=500, detail=f"Failed to sync permission groups: {str(e)}"
        )
