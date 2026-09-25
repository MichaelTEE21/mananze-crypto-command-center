"""Evidence content ingestion boundary for Mananze OS.

This layer converts supplied evidence into analysis-ready content.

It does not:
- decide business truth
- create a Business Twin
- activate capabilities
- authorize actions
- execute external actions

Parsers/adapters can be added behind the EvidenceContentExtractor contract.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

from .evidence_reference import EvidenceReference


SupportedContentType = str


@dataclass(frozen=True)
class EvidenceContent:
    """Analysis-ready content extracted from one evidence item."""

    evidence_id: str
    tenant_id: str
    content_type: SupportedContentType
    content: object
    content_hash: str
    extractor_id: str

    def __post_init__(self) -> None:
        required = (
            ("evidence_id", self.evidence_id),
            ("tenant_id", self.tenant_id),
            ("content_type", self.content_type),
            ("extractor_id", self.extractor_id),
        )

        for name, value in required:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.content_hash, str) or len(self.content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hexadecimal digest")


@dataclass(frozen=True)
class EvidenceExtractionRequest:
    """Request to extract analysis-ready content from evidence."""

    tenant_id: str
    evidence: EvidenceReference
    raw_content: object
    content_type: SupportedContentType

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

        if self.evidence.tenant_id != self.tenant_id:
            raise PermissionError(
                "evidence tenant does not match extraction tenant"
            )

        if (
            not isinstance(self.content_type, str)
            or not self.content_type.strip()
        ):
            raise ValueError("content_type must be a non-empty string")


class EvidenceContentExtractor(Protocol):
    """Contract implemented by evidence extraction adapters."""

    @property
    def extractor_id(self) -> str:
        ...

    @property
    def supported_content_types(self) -> tuple[str, ...]:
        ...

    def extract(
        self,
        request: EvidenceExtractionRequest,
    ) -> object:
        ...


def _content_hash(content: object) -> str:
    """Create a deterministic SHA-256 hash for extracted content."""

    if isinstance(content, bytes):
        material = content
    else:
        material = repr(content).encode("utf-8")

    return hashlib.sha256(material).hexdigest()


class EvidenceContentIngestion:
    """Governed boundary between raw evidence and extracted content."""

    def __init__(self, extractor: EvidenceContentExtractor) -> None:
        self.extractor = extractor

    def ingest(
        self,
        request: EvidenceExtractionRequest,
    ) -> EvidenceContent:
        if request.evidence.tenant_id != request.tenant_id:
            raise PermissionError(
                "cross-tenant evidence ingestion denied"
            )

        extractor_id = self.extractor.extractor_id

        if not isinstance(extractor_id, str) or not extractor_id.strip():
            raise ValueError(
                "extractor_id must be a non-empty string"
            )

        if request.content_type not in self.extractor.supported_content_types:
            raise ValueError(
                f"extractor does not support content type: "
                f"{request.content_type}"
            )

        extracted = self.extractor.extract(request)

        return EvidenceContent(
            evidence_id=request.evidence.evidence_id,
            tenant_id=request.tenant_id,
            content_type=request.content_type,
            content=extracted,
            content_hash=_content_hash(extracted),
            extractor_id=extractor_id,
        )


class PassthroughEvidenceExtractor:
    """Deterministic extractor for already-readable test content.

    Real PDF, DOCX, XLSX, website, and OCR adapters will implement the same
    EvidenceContentExtractor contract later.
    """

    def __init__(
        self,
        *,
        extractor_id: str = "passthrough",
        supported_content_types: tuple[str, ...] = (
            "text/plain",
            "application/json",
            "text/html",
        ),
    ) -> None:
        if not extractor_id.strip():
            raise ValueError("extractor_id must not be blank")

        self._extractor_id = extractor_id
        self._supported_content_types = supported_content_types

    @property
    def extractor_id(self) -> str:
        return self._extractor_id

    @property
    def supported_content_types(self) -> tuple[str, ...]:
        return self._supported_content_types

    def extract(
        self,
        request: EvidenceExtractionRequest,
    ) -> object:
        return request.raw_content


__all__ = [
    "EvidenceContent",
    "EvidenceContentExtractor",
    "EvidenceContentIngestion",
    "EvidenceExtractionRequest",
    "PassthroughEvidenceExtractor",
]
