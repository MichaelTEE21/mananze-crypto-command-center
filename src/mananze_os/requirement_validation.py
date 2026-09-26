"""Mananze OS requirement validation foundation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from mananze_os.requirement import Requirement


RequirementValidationDisposition = Literal[
    "pass",
    "review_required",
    "conflict",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class RequirementValidationFinding:
    """A deterministic validation finding for a requirement."""

    check_id: str
    disposition: RequirementValidationDisposition
    message: str

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("requirement validation check ID is required")

        if not self.disposition.strip():
            raise ValueError("requirement validation disposition is required")

        if self.disposition not in {
            "pass",
            "review_required",
            "conflict",
            "insufficient_evidence",
        }:
            raise ValueError(
                "invalid requirement validation disposition"
            )

        if not self.message.strip():
            raise ValueError("requirement validation message is required")


@dataclass(frozen=True)
class RequirementValidationResult:
    """Immutable validation result for one requirement."""

    validation_id: str
    tenant_id: str
    requirement_id: str
    findings: tuple[RequirementValidationFinding, ...]

    @property
    def passed(self) -> bool:
        return all(
            finding.disposition == "pass"
            for finding in self.findings
        )

    @property
    def requires_review(self) -> bool:
        return any(
            finding.disposition
            in {
                "review_required",
                "conflict",
                "insufficient_evidence",
            }
            for finding in self.findings
        )


class RequirementValidator:
    """Deterministic validation of a business requirement.

    This validator identifies missing, uncertain, or conflicting
    requirement information. It does not guess, calculate,
    quote, procure, approve, or execute.
    """

    def validate(
        self,
        validation_id: str,
        requirement: Requirement,
    ) -> RequirementValidationResult:
        if not validation_id.strip():
            raise ValueError("validation ID is required")

        findings: list[RequirementValidationFinding] = []

        if not requirement.evidence_ids:
            findings.append(
                RequirementValidationFinding(
                    check_id="evidence_presence",
                    disposition="insufficient_evidence",
                    message="requirement has no supporting evidence",
                )
            )
        else:
            findings.append(
                RequirementValidationFinding(
                    check_id="evidence_presence",
                    disposition="pass",
                    message="requirement has supporting evidence",
                )
            )

        if requirement.confirmation_status == "confirmed":
            confirmation_disposition: RequirementValidationDisposition = "pass"
            confirmation_message = "requirement is confirmed"
        elif requirement.confirmation_status == "partially_confirmed":
            confirmation_disposition = "review_required"
            confirmation_message = "requirement is only partially confirmed"
        else:
            confirmation_disposition = "review_required"
            confirmation_message = "requirement is not confirmed"

        findings.append(
            RequirementValidationFinding(
                check_id="confirmation_status",
                disposition=confirmation_disposition,
                message=confirmation_message,
            )
        )

        if requirement.quantity > 0:
            findings.append(
                RequirementValidationFinding(
                    check_id="quantity",
                    disposition="pass",
                    message="requirement quantity is valid",
                )
            )

        if requirement.dimensions.strip():
            findings.append(
                RequirementValidationFinding(
                    check_id="dimensions",
                    disposition="pass",
                    message="requirement dimensions are present",
                )
            )
        else:
            findings.append(
                RequirementValidationFinding(
                    check_id="dimensions",
                    disposition="review_required",
                    message="requirement dimensions are missing",
                )
            )

        return RequirementValidationResult(
            validation_id=validation_id,
            tenant_id=requirement.tenant_id,
            requirement_id=requirement.requirement_id,
            findings=tuple(findings),
        )


__all__ = [
    "RequirementValidationDisposition",
    "RequirementValidationFinding",
    "RequirementValidationResult",
    "RequirementValidator",
]
