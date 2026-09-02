"""Pipeline filter order, DEMO labelling, no-hallucination summarizer, repository schema."""
from __future__ import annotations

from pathlib import Path

from mccc.db import init_db
from mccc.intelligence.pipeline import IntelligencePipeline
from mccc.intelligence.repository import IntelligenceRepository
from mccc.intelligence.summarization_service import SummarizationService


def test_pipeline_demo_seed_and_schema(tmp_path: Path):
    db = tmp_path / "intel.db"
    # init_db hooks IntelligencePipeline.seed_demo_if_empty()
    init_db(db)
    repo = IntelligenceRepository(db)
    assert repo.count_events(is_demo=True) >= 1
    events = repo.list_events(include_demo=True, limit=50)
    assert events
    for ev in events:
        assert ev.is_demo or ev.status == "DEMO" or "DEMO" in ev.title.upper()
        assert ev.source_type
        assert ev.discovered_at
        assert ev.confidence
        assert isinstance(ev.importance, int)
    for fr in repo.list_funding():
        amt = str(fr.get("amount") or "")
        assert amt in ("Not disclosed", "Unknown", "Unconfirmed") or bool(fr.get("is_demo"))
        assert amt not in ("$10M", "$100,000,000")


def test_pipeline_idempotent_dedupe(tmp_path: Path):
    db = tmp_path / "intel2.db"
    init_db(db)
    pipe = IntelligencePipeline(db)
    # First explicit run after seed should skip existing fingerprints
    r2 = pipe.run(include_demo=True, include_live_rss=False)
    assert r2.stored == 0
    assert r2.skipped_existing >= 1
    # Fresh repo path without prior seed: use ensure_ready only
    db3 = tmp_path / "intel2b.db"
    pipe3 = IntelligencePipeline(db3)
    r1 = pipe3.run(include_demo=True, include_live_rss=False)
    assert r1.stored >= 1
    r1b = pipe3.run(include_demo=True, include_live_rss=False)
    assert r1b.stored == 0


def test_summarizer_no_hallucination_on_incomplete():
    s = SummarizationService(use_llm=False)
    s.clear_cache()
    out = s.summarize(title="Only title", body="", fingerprint="fp-empty", is_demo=True)
    assert "Only title" in out or out.startswith("[DEMO]")
    out2 = s.summarize(
        title="T",
        body="First sentence about a protocol. Second sentence continues.",
        fingerprint="fp-body",
        is_demo=False,
    )
    assert "First sentence" in out2
    assert "Series B" not in out2


def test_candidates_not_auto_verified(tmp_path: Path):
    db = tmp_path / "intel3.db"
    pipe = IntelligencePipeline(db)
    pipe.run(include_demo=True, include_live_rss=False)
    cands = IntelligenceRepository(db).list_candidates()
    for c in cands:
        assert c["status"] == "DISCOVERED"


def test_ingestion_runs_recorded(tmp_path: Path):
    db = tmp_path / "intel4.db"
    pipe = IntelligencePipeline(db)
    pipe.run(include_demo=True, include_live_rss=False)
    runs = IntelligenceRepository(db).list_runs(limit=5)
    assert runs
    assert runs[0]["status"] == "ok"
