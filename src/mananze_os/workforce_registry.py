"""Mananze OS workforce role registry foundation."""

from mananze_os.workforce_role import WorkforceRole


class WorkforceRegistry:
    """Registry of workforce roles available to Mananze OS."""

    def __init__(self) -> None:
        self._roles: dict[str, WorkforceRole] = {}

    def register(self, role: WorkforceRole) -> None:
        if role.role_id in self._roles:
            raise ValueError(
                f"workforce role already registered: {role.role_id}"
            )

        self._roles[role.role_id] = role

    def get(self, role_id: str) -> WorkforceRole:
        try:
            return self._roles[role_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown workforce role: {role_id}"
            ) from exc

    def list_all(self) -> tuple[WorkforceRole, ...]:
        return tuple(self._roles.values())


__all__ = ["WorkforceRegistry"]
