"""Intelligence Report subsystem — Search → Analyse → Understand.

Architecture: Providers → Normalisation → Analytics → Intelligence → Report → Education.
"""
from __future__ import annotations

from mananze_hub.crypto_web3.intelligence.report.engine import ReportEngine
from mananze_hub.crypto_web3.intelligence.report.schema import (
    REPORT_DISCLAIMER,
    DataMode,
    DataQuality,
    EntityType,
    IntelligenceReport,
    METRIC_EXPLAINERS,
    SUPPORTED_ENTITY_TYPES,
)
from mananze_hub.crypto_web3.intelligence.report.validators import ValidatedQuery, validate_report_query

__all__ = [
    "ReportEngine",
    "IntelligenceReport",
    "EntityType",
    "DataMode",
    "DataQuality",
    "SUPPORTED_ENTITY_TYPES",
    "METRIC_EXPLAINERS",
    "REPORT_DISCLAIMER",
    "ValidatedQuery",
    "validate_report_query",
]
