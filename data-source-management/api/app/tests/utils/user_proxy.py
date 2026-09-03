from __future__ import annotations


class UserProxy:
    """Mimics User without SQLAlchemy session binding.
    Used in tests to avoid session conflicts between the test
    fixture session and FastAPI's internal session."""

    def __init__(self, user, permission_group_ids: list[int]):
        self.id = user.id
        self.sub = user.sub
        self.username = user.username
        self.email = user.email
        self.is_active = user.is_active
        self.is_superuser = user.is_superuser
        self._permission_group_ids = permission_group_ids

    @property
    def permission_group_ids(self) -> list[int]:
        return self._permission_group_ids
