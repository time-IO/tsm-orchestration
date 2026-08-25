from fastapi import HTTPException
from access_scope import AccessScope


class RepositoryValidator:

    @staticmethod
    def check_payload_access_scope(
        permission_group_id_to_check: int, access_scope: AccessScope
    ):
        if not access_scope.can_access_permission_group(permission_group_id_to_check):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: user does not belong to that permission group.",
            )
