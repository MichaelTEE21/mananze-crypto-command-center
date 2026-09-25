"""Governed tenant-specific capability activation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.business_twin import BusinessTwin
from mananze_os.capability_registry import (
    CapabilityRegistry,
    default_capability_registry,
)
from mananze_os.compiler import CompiledRequirement, IntelligenceCompiler
from mananze_os.work_order import WorkOrder


ActivationStatus = Literal["active", "conditional", "unavailable"]


@dataclass(frozen=True)
class CapabilityActivation:
    capability_id: str
    status: ActivationStatus
    reason: str
    supporting_truth_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityActivationPlan:
    tenant_id: str
    twin_id: str
    activations: tuple[CapabilityActivation, ...]

    @property
    def active_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            activation.capability_id
            for activation in self.activations
            if activation.status == "active"
        )

    @property
    def conditional_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            activation.capability_id
            for activation in self.activations
            if activation.status == "conditional"
        )

    @property
    def unavailable_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            activation.capability_id
            for activation in self.activations
            if activation.status == "unavailable"
        )


class CapabilityActivationEngine:
    """
    Determines which registered capabilities are supported by a
    tenant's Business Twin.

    This boundary does not execute actions, grant permissions, or
    bypass Policy, Authorization, or Approval.
    """

    _EVIDENCE_RULES: dict[str, tuple[str, ...]] = {
        "marketing": (
            "services",
            "products",
            "commercial_rules",
            "relationships",
        ),
        "lead_generation": (
            "services",
            "products",
            "relationships",
        ),
        "sales": (
            "services",
            "products",
            "commercial_rules",
            "processes",
        ),
        "appointment_booking": (
            "services",
            "processes",
            "systems",
            "relationships",
        ),
        "customer_communications": (
            "relationships",
            "systems",
            "processes",
            "policies",
        ),
        "retention": (
            "relationships",
            "processes",
            "services",
        ),
        "revenue": (
            "commercial_rules",
            "services",
            "products",
        ),
        "operations": (
            "processes",
            "services",
            "systems",
        ),
        "logistics": (
            "services",
            "processes",
            "locations",
            "relationships",
            "dependencies",
        ),
        "fleet": (
            "services",
            "processes",
            "systems",
            "dependencies",
        ),
        "cost_analysis": (
            "commercial_rules",
            "processes",
            "systems",
            "dependencies",
        ),
        "reporting": (
            "processes",
            "systems",
            "policies",
            "compliance",
        ),
        "receivables": (
            "commercial_rules",
            "relationships",
            "processes",
            "systems",
        ),
        "payment_collection": (
            "commercial_rules",
            "relationships",
            "processes",
            "systems",
        ),
    }

    def __init__(
        self,
        registry: CapabilityRegistry | None = None,
        compiler: IntelligenceCompiler | None = None,
    ) -> None:
        self.registry = registry or default_capability_registry()
        self.compiler = compiler or IntelligenceCompiler(self.registry)

    @staticmethod
    def _records(twin: BusinessTwin, field_name: str) -> list[dict]:
        value = getattr(twin, field_name)

        if field_name == "identity":
            return list(value.get("records", []))

        return list(value)

    @staticmethod
    def _truth_ids(records: list[dict]) -> tuple[str, ...]:
        ids: list[str] = []

        for record in records:
            observation_ids = record.get("observation_ids", ())
            ids.extend(observation_ids)

        return tuple(sorted(set(ids)))

    def _activate_one(
        self,
        twin: BusinessTwin,
        capability_id: str,
    ) -> CapabilityActivation:
        capability = self.registry.get(capability_id)

        required_buckets = self._EVIDENCE_RULES.get(
            capability.capability_id,
            (),
        )

        supporting_records: list[dict] = []

        for bucket in required_buckets:
            supporting_records.extend(
                self._records(twin, bucket)
            )

        supporting_truth_ids = self._truth_ids(supporting_records)

        if not supporting_records:
            return CapabilityActivation(
                capability_id=capability.capability_id,
                status="unavailable",
                reason=(
                    "No Business Twin evidence currently supports "
                    f"{capability.capability_id}."
                ),
                supporting_truth_ids=(),
            )

        if twin.conflicts:
            return CapabilityActivation(
                capability_id=capability.capability_id,
                status="conditional",
                reason=(
                    "Business Twin contains unresolved conflicts; "
                    "capability requires controlled confirmation."
                ),
                supporting_truth_ids=supporting_truth_ids,
            )

        if twin.status in {"stale", "incomplete"}:
            return CapabilityActivation(
                capability_id=capability.capability_id,
                status="conditional",
                reason=(
                    f"Business Twin status is {twin.status}; "
                    "capability applicability requires confirmation."
                ),
                supporting_truth_ids=supporting_truth_ids,
            )

        return CapabilityActivation(
            capability_id=capability.capability_id,
            status="active",
            reason=(
                f"Business Twin evidence supports "
                f"{capability.capability_id} applicability."
            ),
            supporting_truth_ids=supporting_truth_ids,
        )

    def activate(
        self,
        twin: BusinessTwin,
        candidate_capability_ids: tuple[str, ...],
    ) -> CapabilityActivationPlan:
        if not twin.tenant_id.strip():
            raise ValueError("twin tenant_id is required")

        if not twin.twin_id.strip():
            raise ValueError("twin_id is required")

        activations = tuple(
            self._activate_one(twin, capability_id)
            for capability_id in dict.fromkeys(candidate_capability_ids)
        )

        return CapabilityActivationPlan(
            tenant_id=twin.tenant_id,
            twin_id=twin.twin_id,
            activations=activations,
        )

    def compile_active_requirements(
        self,
        twin: BusinessTwin,
        work_order_id: str,
        objective: str,
        plan: CapabilityActivationPlan,
    ) -> tuple[CompiledRequirement, ...]:
        if plan.tenant_id != twin.tenant_id:
            raise PermissionError(
                "capability activation tenant mismatch"
            )

        if plan.twin_id != twin.twin_id:
            raise PermissionError(
                "capability activation twin mismatch"
            )

        work_order = WorkOrder(
            work_order_id=work_order_id,
            tenant_id=twin.tenant_id,
            objective=objective,
        )

        compiled = self.compiler.compile(
            work_order,
            candidate_capability_ids=plan.active_capability_ids,
        )

        return compiled.requirements


__all__ = [
    "ActivationStatus",
    "CapabilityActivation",
    "CapabilityActivationPlan",
    "CapabilityActivationEngine",
]
