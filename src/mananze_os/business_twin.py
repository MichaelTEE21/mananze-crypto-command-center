from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Literal


TwinStatus = Literal["active", "conflicted", "incomplete", "stale"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{k}:{_canonical(value[k])}" for k in sorted(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canonical(v) for v in value) + "]"
    return repr(value)


def _twin_id(tenant_id: str, truths: Iterable[Any]) -> str:
    material = tenant_id + "|" + "|".join(
        sorted(
            f"{truth.subject}:{_canonical(truth.value)}:{truth.status}"
            for truth in truths
        )
    )
    return "twin-" + sha256(material.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class BusinessTwin:
    twin_id: str
    tenant_id: str
    status: TwinStatus
    identity: dict[str, Any]
    services: list[dict[str, Any]]
    products: list[dict[str, Any]]
    locations: list[dict[str, Any]]
    processes: list[dict[str, Any]]
    commercial_rules: list[dict[str, Any]]
    people_and_roles: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    suppliers: list[dict[str, Any]]
    systems: list[dict[str, Any]]
    policies: list[dict[str, Any]]
    compliance: list[dict[str, Any]]
    capabilities: list[dict[str, Any]]
    dependencies: list[dict[str, Any]]
    gaps: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    truth_ids: tuple[str, ...]
    generated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.twin_id.strip():
            raise ValueError("twin_id is required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.truth_ids:
            raise ValueError("Business Twin requires Business Truth")

        if self.status not in {
            "active",
            "conflicted",
            "incomplete",
            "stale",
        }:
            raise ValueError("invalid Business Twin status")


class BusinessTwinBuilder:
    """
    Constructs a tenant-scoped Business Twin exclusively from
    governed Business Truth records.

    This class does not invent business facts and does not resolve
    conflicts itself. Conflict resolution belongs to Business Truth.
    """

    _FIELD_MAP = {
        "identity": "identity",
        "service": "services",
        "services": "services",
        "product": "products",
        "products": "products",
        "location": "locations",
        "locations": "locations",
        "process": "processes",
        "processes": "processes",
        "pricing": "commercial_rules",
        "price": "commercial_rules",
        "commercial_rule": "commercial_rules",
        "commercial_rules": "commercial_rules",
        "person": "people_and_roles",
        "people": "people_and_roles",
        "role": "people_and_roles",
        "people_and_roles": "people_and_roles",
        "relationship": "relationships",
        "relationships": "relationships",
        "supplier": "suppliers",
        "suppliers": "suppliers",
        "system": "systems",
        "systems": "systems",
        "policy": "policies",
        "policies": "policies",
        "compliance": "compliance",
        "capability": "capabilities",
        "capabilities": "capabilities",
        "dependency": "dependencies",
        "dependencies": "dependencies",
    }

    def build(
        self,
        *,
        tenant_id: str,
        truths: Iterable[Any],
    ) -> BusinessTwin:
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")

        truth_list = list(truths)

        if not truth_list:
            raise ValueError(
                "Business Twin cannot be created without Business Truth"
            )

        for truth in truth_list:
            if truth.tenant_id != tenant_id:
                raise PermissionError(
                    "Business Truth tenant does not match Business Twin tenant"
                )

        buckets: dict[str, list[dict[str, Any]]] = {
            field_name: [] for field_name in (
                "identity",
                "services",
                "products",
                "locations",
                "processes",
                "commercial_rules",
                "people_and_roles",
                "relationships",
                "suppliers",
                "systems",
                "policies",
                "compliance",
                "capabilities",
                "dependencies",
            )
        }

        gaps: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        stale = False

        for truth in truth_list:
            subject = truth.subject.strip().lower()
            field_name = self._FIELD_MAP.get(subject)

            record = {
                "subject": truth.subject,
                "value": truth.value,
                "status": truth.status,
                "confidence": truth.confidence,
                "source_type": truth.source_type,
                "source_reference": truth.source_reference,
                "observation_ids": list(truth.observation_ids),
                "effective_at": truth.effective_at,
                "resolved_at": truth.resolved_at,
            }

            if truth.status == "conflicting":
                conflicts.append(record)
                continue

            if truth.status == "stale":
                stale = True

            if field_name is None:
                gaps.append(record)
                continue

            if field_name == "identity":
                buckets[field_name].append(record)
            else:
                buckets[field_name].append(record)

        if conflicts:
            status: TwinStatus = "conflicted"
        elif stale:
            status = "stale"
        elif gaps:
            status = "incomplete"
        else:
            status = "active"

        return BusinessTwin(
            twin_id=_twin_id(tenant_id, truth_list),
            tenant_id=tenant_id,
            status=status,
            identity={
                "records": buckets["identity"],
            },
            services=buckets["services"],
            products=buckets["products"],
            locations=buckets["locations"],
            processes=buckets["processes"],
            commercial_rules=buckets["commercial_rules"],
            people_and_roles=buckets["people_and_roles"],
            relationships=buckets["relationships"],
            suppliers=buckets["suppliers"],
            systems=buckets["systems"],
            policies=buckets["policies"],
            compliance=buckets["compliance"],
            capabilities=buckets["capabilities"],
            dependencies=buckets["dependencies"],
            gaps=gaps,
            conflicts=conflicts,
            truth_ids=tuple(sorted(truth.truth_id for truth in truth_list)),
        )


class BusinessTwinRegistry:
    """Tenant-isolated storage for constructed Business Twins."""

    def __init__(self) -> None:
        self._twins: dict[tuple[str, str], BusinessTwin] = {}

    def put(self, twin: BusinessTwin) -> None:
        self._twins[(twin.tenant_id, twin.twin_id)] = twin

    def get(self, twin_id: str, tenant_id: str) -> BusinessTwin:
        twin = self._twins.get((tenant_id, twin_id))

        if twin is None:
            raise KeyError("Business Twin not found")

        return twin

    def list_tenant(self, tenant_id: str) -> list[BusinessTwin]:
        return [
            twin
            for (stored_tenant, _), twin in self._twins.items()
            if stored_tenant == tenant_id
        ]


__all__ = [
    "BusinessTwin",
    "BusinessTwinBuilder",
    "BusinessTwinRegistry",
    "TwinStatus",
]
