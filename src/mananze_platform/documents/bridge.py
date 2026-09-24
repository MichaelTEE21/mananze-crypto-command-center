"""Document-to-intake bridge.

A document becomes business intake only after it has an explicit tenant,
actor and evidence reference.
"""
from __future__ import annotations

from mananze_platform.documents.contracts import (
    BusinessDocument,
    DocumentEvidence,
)
from mananze_platform.intake import BusinessIntake, IntakeSource


def evidence_to_intake(
    document: BusinessDocument,
    evidence: DocumentEvidence,
) -> BusinessIntake:
    if document.tenant_id != evidence.tenant_id:
        raise PermissionError("document/evidence tenant mismatch")

    if document.document_id != evidence.document_id:
        raise ValueError("document/evidence ID mismatch")

    return BusinessIntake(
        tenant_id=document.tenant_id,
        actor_id=document.actor_id,
        source=IntakeSource.DOCUMENT,
        content=evidence.content,
        intake_id=f"intake:{document.document_id}",
    )
