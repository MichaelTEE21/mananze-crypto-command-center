"""Mananze OS obligation registry foundation."""

from mananze_os.obligation_intelligence import (
    Obligation,
    ObligationDependency,
)


class ObligationRegistry:
    """Tenant-aware registry for authorised obligation records."""

    def __init__(self) -> None:
        self._obligations: dict[str, Obligation] = {}
        self._dependencies: dict[str, ObligationDependency] = {}

    def register(self, obligation: Obligation) -> None:
        existing = self._obligations.get(obligation.obligation_id)

        if existing is not None:
            raise ValueError(
                f"obligation already registered: "
                f"{obligation.obligation_id}"
            )

        self._obligations[obligation.obligation_id] = obligation

    def get(self, obligation_id: str) -> Obligation:
        if not obligation_id.strip():
            raise ValueError("obligation_id is required")

        try:
            return self._obligations[obligation_id]
        except KeyError as exc:
            raise KeyError(
                f"unknown obligation: {obligation_id}"
            ) from exc

    def list_for_tenant(
        self,
        tenant_id: str,
    ) -> tuple[Obligation, ...]:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        return tuple(
            obligation
            for obligation in self._obligations.values()
            if obligation.tenant_id == tenant_id
        )

    def list_all(self) -> tuple[Obligation, ...]:
        return tuple(self._obligations.values())

    def register_dependency(
        self,
        dependency: ObligationDependency,
    ) -> None:
        existing = self._dependencies.get(dependency.dependency_id)

        if existing is not None:
            raise ValueError(
                f"dependency already registered: "
                f"{dependency.dependency_id}"
            )

        if dependency.obligation_id not in self._obligations:
            raise KeyError(
                f"unknown obligation: {dependency.obligation_id}"
            )

        obligation = self._obligations[dependency.obligation_id]

        if obligation.tenant_id != dependency.tenant_id:
            raise ValueError(
                "dependency tenant does not match obligation tenant"
            )

        self._dependencies[dependency.dependency_id] = dependency

    def list_dependencies_for_obligation(
        self,
        obligation_id: str,
    ) -> tuple[ObligationDependency, ...]:
        if not obligation_id.strip():
            raise ValueError("obligation_id is required")

        return tuple(
            dependency
            for dependency in self._dependencies.values()
            if dependency.obligation_id == obligation_id
        )


__all__ = ["ObligationRegistry"]
