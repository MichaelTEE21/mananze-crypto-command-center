"""Mananze OS execution verification contract."""

from dataclasses import dataclass

from mananze_os.execution_evidence import ExecutionEvidence
from mananze_os.execution_state import ExecutionState


@dataclass(frozen=True)
class ExecutionVerification:
    execution_id: str
    verified: bool
    reasons: tuple[str, ...]


class ExecutionVerifier:
    """Verify execution state and evidence before completion."""

    def verify(
        self,
        state: ExecutionState,
        evidence: tuple[ExecutionEvidence, ...],
    ) -> ExecutionVerification:
        if not state.execution_id.strip():
            raise ValueError("execution_id is required")

        reasons: list[str] = []

        for item in evidence:
            if item.execution_id != state.execution_id:
                reasons.append(
                    "evidence execution ID mismatch"
                )
                break

        if not reasons and state.status == "completed":
            required_actions = {
                "policy_decision",
                "authorization_decision",
                "controlled_execution",
            }

            evidence_actions = {
                item.action
                for item in evidence
            }

            missing_actions = required_actions - evidence_actions

            if missing_actions:
                reasons.append(
                    "missing required evidence: "
                    + ", ".join(sorted(missing_actions))
                )

        if reasons:
            verified = False
        else:
            verified = True
            reasons.append(
                "execution state and evidence verified"
            )

        return ExecutionVerification(
            execution_id=state.execution_id,
            verified=verified,
            reasons=tuple(reasons),
        )


__all__ = [
    "ExecutionVerification",
    "ExecutionVerifier",
]
