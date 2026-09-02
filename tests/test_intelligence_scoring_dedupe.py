"""Scoring, source tier confidence, dedupe clustering."""
from __future__ import annotations

from mccc.intelligence.deduplication_service import DeduplicationService
from mccc.intelligence.schema import RawDocument, SourceTier
from mccc.intelligence.scoring_service import ScoringService


def test_scoring_demo_never_verified():
    s = ScoringService()
    r = s.score(source_tier=1, category="breaking", is_demo=True, has_source_url=True)
    assert r.confidence == "UNCONFIRMED"
    assert r.importance <= 55


def test_scoring_official_live_verified():
    s = ScoringService()
    r = s.score(
        source_tier=int(SourceTier.OFFICIAL),
        category="technology",
        is_demo=False,
        has_source_url=True,
    )
    assert r.confidence == "VERIFIED"


def test_dedupe_drops_exact_duplicates():
    d = DeduplicationService()
    docs = [
        RawDocument(title="Same Title", body="alpha", source_url="https://example.com/a"),
        RawDocument(title="Same Title", body="alpha", source_url="https://example.com/a"),
        RawDocument(title="Other", body="beta", source_url="https://example.com/b"),
    ]
    res = d.dedupe_raw(docs)
    assert len(res.unique_docs) == 2
    assert res.dropped == 1
