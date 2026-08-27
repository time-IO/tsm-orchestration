from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import User


@dataclass(frozen=True)
class AccessScope:
    permission_group_ids: list[int]
    is_superuser: bool = False

    @classmethod
    def from_user(cls, user: User) -> AccessScope:
        return cls(
            permission_group_ids=user.permission_group_ids,
            is_superuser=user.is_superuser,
        )

    def can_access_permission_group(self, permission_group_id: int) -> bool:
        return self.is_superuser or permission_group_id in self.permission_group_ids
