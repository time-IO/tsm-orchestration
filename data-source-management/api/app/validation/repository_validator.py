from fastapi import HTTPException


class RepositoryValidator:
    @staticmethod
    def check_payload_permission_group(
        permission_group_id_to_check: int, permission_group_ids: list[int]
    ):
        if permission_group_id_to_check not in permission_group_ids:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: user does not belong to that permission group.",
            )
