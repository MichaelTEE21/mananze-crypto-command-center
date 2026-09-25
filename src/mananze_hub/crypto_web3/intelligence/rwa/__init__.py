"""RWA (Real-World Assets) intelligence vertical — MCCC only.

Extends Intelligence Agent with taxonomy, profiles, classification, DEMO seeds,
disclosure-based risk framework, and dashboard/search hooks. Not trading/custody.
"""
from __future__ import annotations

from mccc.intelligence.rwa.classification import RWAClassification, RWAClassificationService
from mccc.intelligence.rwa.repository import RWARepository
from mccc.intelligence.rwa.schema import (
    ClaimProvenance,
    RiskDisclosure,
    RWAProfile,
    TokenizedAssetValue,
)
from mccc.intelligence.rwa.service import RWASeedResult, RWAService
from mccc.intelligence.rwa.taxonomy import (
    RWA_DISCLAIMER,
    RWACategory,
    RWAEventType,
    TOP_LEVEL_CATEGORY,
    AssetValueType,
    DisclosureStatus,
    VerificationStatus,
    all_rwa_categories,
    all_rwa_event_types,
)

__all__ = [
    "RWAService",
    "RWASeedResult",
    "RWARepository",
    "RWAProfile",
    "TokenizedAssetValue",
    "ClaimProvenance",
    "RiskDisclosure",
    "RWAClassification",
    "RWAClassificationService",
    "RWACategory",
    "RWAEventType",
    "AssetValueType",
    "DisclosureStatus",
    "VerificationStatus",
    "TOP_LEVEL_CATEGORY",
    "RWA_DISCLAIMER",
    "all_rwa_categories",
    "all_rwa_event_types",
]
