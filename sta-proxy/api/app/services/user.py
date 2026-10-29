from services.dsm_api import (
    dsm_error_to_http_exception,
    fetch_dsm_api_or_raise,
    require_authorization,
)
from models.user import UserPublic

ACTION = "fetching user info"


async def get_me_service(authorization: str | None) -> UserPublic:
    authorization = require_authorization(authorization)
    data = await fetch_dsm_api_or_raise("/me/", authorization, ACTION)
    try:
        return UserPublic.model_validate(data)
    except ValueError as e:
        raise dsm_error_to_http_exception(e, ACTION)
