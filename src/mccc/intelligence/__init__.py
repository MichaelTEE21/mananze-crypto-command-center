"""MCCC Intelligence Agent — discovery/structuring engine (not a chatbot).

Phase 1 foundation + RWA vertical: modular pipeline INGEST→NORMALIZE→DEDUPE→CLASSIFY→EXTRACT
→SCORE→SUMMARIZE→STORE, SQLite repository (production-swappable), DEMO/LIVE
separation, and Intelligence Center UI over sourced events.
"""
from __future__ import annotations

from mccc.intelligence.pipeline import IntelligencePipeline, PipelineResult
from mccc.intelligence.repository import IntelligenceRepository
from mccc.intelligence.schema import (
    Confidence,
    EventCategory,
    IntelligenceEvent,
    SourceTier,
    DISCLAIMER,
)
from mccc.intelligence.source_service import SourceService, ROBOTS_TOS_STANCE

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
]
