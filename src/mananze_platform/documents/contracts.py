"""Tenant-scoped document intake contracts.

Documents are treated as untrusted input and evidence sources.
This module does not execute document contents and does not grant permissions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class DocumentKind(StrEnum):
    UNKNOWN = "unknown"
    BUSINESS_PROFILE = "business_profile"
    INVOICE = "invoice"
    CONTRACT = "contract"
    MARKETING = "marketing"
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    OTHER = "other"


@dataclass(frozen=True)
class BusinessDocument:
    """Metadata for a document supplied by a tenant."""

    tenant_id: str
    actor_id: str
    filename: str
    content_type: str
    size_bytes: int
    document_id: str = field(
        default_factory=lambda: f"doc:{uuid4().hex}"
    )
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    kind: DocumentKind = DocumentKind.UNKNOWN
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")
        if not self.filename.strip():
            raise ValueError("filename is required")
        if not self.content_type.strip():
            raise ValueError("content_type is required")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")
        if self.sha256 is not None and len(self.sha256) != 64:
            raise ValueError("sha256 must be a 64-character hexadecimal digest")


@dataclass(frozen=True)
class DocumentEvidence:
    """Extracted document content with explicit provenance."""

    tenant_id: str
    document_id: str
    content: str
    extraction_method: str
    evidence_ref: str
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.document_id.strip():
            raise ValueError("document_id is required")
        if not self.content.strip():
            raise ValueError("content is required")
        if not self.extraction_method.strip():
            raise ValueError("extraction_method is required")
        if not self.evidence_ref.strip():
            raise ValueError("evidence_ref is required")


def create_document_evidence(
    document: BusinessDocument,
    content: str,
    *,
    extraction_method: str = "provided_text",
) -> DocumentEvidence:
    """Create tenant-scoped evidence from already validated text.

    Actual file parsing/security scanning will be added at the ingestion
    boundary. This function never executes content.
    """
    return DocumentEvidence(
        tenant_id=document.tenant_id,
        document_id=document.document_id,
        content=content,
        extraction_method=extraction_method,
        evidence_ref=f"evidence:{document.document_id}",
    )
