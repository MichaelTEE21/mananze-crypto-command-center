"""MCCC Intelligence Agent — discovery/structuring engine (not a chatbot).

Phase 1 foundation + RWA vertical: modular pipeline INGEST→NORMALIZE→DEDUPE→CLASSIFY→EXTRACT
→SCORE→SUMMARIZE→STORE, SQLite repository (production-swappable), DEMO/LIVE
separation, Intelligence Center UI over sourced events, plus Intelligence Report engine
(Providers→Normalisation→Analytics→Report) for wallet/token/project/protocol/contract/RWA.
"""
from __future__ import annotations

from mananze_hub.crypto_web3.intelligence.pipeline import IntelligencePipeline, PipelineResult
from mananze_hub.crypto_web3.intelligence.repository import IntelligenceRepository
from mananze_hub.crypto_web3.intelligence.schema import (
    Confidence,
    EventCategory,
    IntelligenceEvent,
    SourceTier,
    DISCLAIMER,
)
from mananze_hub.crypto_web3.intelligence.source_service import SourceService, ROBOTS_TOS_STANCE
from mananze_hub.crypto_web3.intelligence.report import ReportEngine, IntelligenceReport, REPORT_DISCLAIMER as REPORT_ENGINE_DISCLAIMER

__all__ = [
    "IntelligencePipeline",
    "PipelineResult",
    "IntelligenceRepository",
    "IntelligenceEvent",
    "SourceService",
    "SourceTier",
    "EventCategory",
    "Confidence",
    "DISCLAIMER",
    "ROBOTS_TOS_STANCE",
    "ReportEngine",
    "IntelligenceReport",
    "REPORT_ENGINE_DISCLAIMER",
]
