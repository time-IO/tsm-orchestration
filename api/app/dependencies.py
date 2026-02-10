from fastapi import Depends, HTTPException
from sqlmodel import Session, create_engine, select
from .config import settings
from .auth import oidc, OIDCError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models.user import User


bearer_scheme = HTTPBearer(auto_error=False)

engine = create_engine(str(settings.DATABASE_URI))

def get_session():
    with Session(engine) as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session = Depends(get_session),
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

def get_or_create_user(
    *,
    session,
    claims: dict,
    access_token: str
):
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
        is_superuser=False
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user
