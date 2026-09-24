"""MANANZE HUB capability catalog validation."""

from mananze_os.capability_registry import CapabilityRegistry

from .catalog import CAPABILITIES, HubCapability


def validate_catalog(
    capabilities: tuple[HubCapability, ...] = CAPABILITIES,
    os_registry: CapabilityRegistry | None = None,
) -> tuple[str, ...]:
    """Validate Hub capability manifests against the authoritative OS registry.

    This function validates declarations only. It does not compile work,
    select execution plans, authorize actions, or execute capabilities.
    """
    errors: list[str] = []

    capability_ids = tuple(
        capability.capability_id for capability in capabilities
    )

    seen_ids: set[str] = set()

    for capability in capabilities:
        capability_id = capability.capability_id

        if capability_id in seen_ids:
            errors.append(
                f"duplicate capability_id: {capability_id}"
            )
        seen_ids.add(capability_id)

    capability_id_set = set(capability_ids)

    for capability in capabilities:
        for dependency in capability.dependencies:
            if dependency not in capability_id_set:
                errors.append(
                    f"{capability.capability_id}: "
                    f"unknown dependency: {dependency}"
                )

    if os_registry is not None:
        for capability in capabilities:
            for os_capability_id in capability.os_capability_ids:
                try:
                    os_registry.get(os_capability_id)
                except KeyError:
                    errors.append(
                        f"{capability.capability_id}: "
                        f"unknown OS capability: {os_capability_id}"
                    )

    return tuple(errors)


def assert_valid_catalog(
    capabilities: tuple[HubCapability, ...] = CAPABILITIES,
    os_registry: CapabilityRegistry | None = None,
) -> None:
    """Raise ValueError when the Hub capability catalog is invalid."""
    errors = validate_catalog(
        capabilities=capabilities,
        os_registry=os_registry,
    )

    if errors:
        raise ValueError(
            "invalid MANANZE HUB capability catalog:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


__all__ = [
    "validate_catalog",
    "assert_valid_catalog",
]
