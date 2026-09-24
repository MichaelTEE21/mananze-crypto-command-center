"""Mananze OS input gate foundation service."""

from mananze_os.input_request import InputRequest
from mananze_os.work_order import WorkOrder


class InputGate:
    """Validate client requests and create controlled work orders."""

    def accept(self, request: InputRequest) -> WorkOrder:
        if not request.request_id.strip():
            raise ValueError("request_id is required")

        if not request.tenant_id.strip():
            raise ValueError("tenant_id is required")

        if not request.actor_id.strip():
            raise ValueError("actor_id is required")

        if not request.objective.strip():
            raise ValueError("objective is required")

        candidate_capability_ids = tuple(
            capability_id.strip()
            for capability_id in request.candidate_capability_ids
        )

        if any(not capability_id for capability_id in candidate_capability_ids):
            raise ValueError("candidate_capability_ids cannot contain blank values")

        if len(candidate_capability_ids) != len(set(candidate_capability_ids)):
            raise ValueError("candidate_capability_ids cannot contain duplicates")

        return WorkOrder(
            work_order_id=request.request_id,
            tenant_id=request.tenant_id,
            objective=request.objective.strip(),
            candidate_capability_ids=candidate_capability_ids,
        )


__all__ = ["InputGate"]
