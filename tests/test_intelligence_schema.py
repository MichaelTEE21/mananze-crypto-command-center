"""Schema / enum / latency / event provenance tests."""
from __future__ import annotations

from mccc.intelligence.repository import compute_discovery_latency_seconds
from mccc.intelligence.schema import (
    Confidence,
    EventCategory,
    ImportanceBand,
    IntelligenceEvent,
    SourceTier,
    content_fingerprint,
    importance_band,
)


def test_source_tiers_ordered():
    assert int(SourceTier.OFFICIAL) == 1
    assert int(SourceTier.UNVERIFIED) == 5


def test_importance_bands():
    assert importance_band(90) == ImportanceBand.CRITICAL
    assert importance_band(65) == ImportanceBand.HIGH
    assert importance_band(45) == ImportanceBand.MEDIUM
    assert importance_band(10) == ImportanceBand.LOW


def test_event_provenance_fields_present():
    ev = IntelligenceEvent(
        id="e1",
        title="[DEMO] sample",
        summary="DEMO summary",
        category=EventCategory.BREAKING.value,
        source_url="https://example.com/demo",
        source_type="demo",
        published_at="2026-09-01T10:00:00+00:00",
        discovered_at="2026-09-01T10:05:00+00:00",
        confidence=Confidence.UNCONFIRMED.value,
        importance=40,
        is_demo=True,
    )
    d = ev.to_dict()
    for key in (
        "source_url",
        "source_type",
        "published_at",
        "discovered_at",
        "confidence",
        "importance",
    ):
        assert key in d and d[key] not in (None, "")


def test_discovery_latency():
    lat = compute_discovery_latency_seconds(
        "2026-09-01T10:00:00+00:00",
        "2026-09-01T10:05:00+00:00",
    )
    assert lat == 300.0
    assert compute_discovery_latency_seconds("", "2026-09-01T10:00:00+00:00") is None


def test_fingerprint_stable():
    a = content_fingerprint("Hello World", "https://x.test/a", "body")
    b = content_fingerprint("hello   world", "https://x.test/a/", "body")
    assert a == b
