# MCCC Intelligence Agent — Phase 1 Report

## Outcome

Phase 0 audit + Phase 1 foundation shipped locally on `/workspace/mccc` (branched from `b42e2de` / MCCC 2.0.0). Version **2.1.0**. **Not pushed** (parent / ENELO pushes).

Intelligence Agent is an **engine** (discover → structure → store), **not a chatbot**. The AI Assistant remains separate and may later brief from this DB (“What happened while I was away?”).

## How to run

```powershell
cd \path\to\mccc
.\START.ps1
# sidebar → Intelligence Center
```

Linux:

```bash
cd /workspace/mccc
.venv/bin/python -m streamlit run app.py
.venv/bin/pytest -q
```

## Non-negotiables covered

1. Schema: `intelligence_events`, `intelligence_sources`, `funding_rounds`, `intelligence_candidates`, `narratives`, `intelligence_watchlist`, `ingestion_runs` (+ integrate Add-to-Project → existing `projects`)
2. Pipeline: INGEST → NORMALIZE → DEDUPE → CLASSIFY → EXTRACT → SCORE → SUMMARIZE → STORE
3. No fabricated funding/investors/TGE/airdrops/prices
4. DEMO/SYNTHETIC visibly labelled; not mixed as live
5. UI sections: Breaking | New Projects | Funding | Airdrop Signals | Token Events | Trending Narratives | Watchlist
6. Provenance: source_url, source_type, published_at, discovered_at, confidence, importance (+ discovery_latency)
7. Provider interfaces (RSS / DEMO / stub); fixtures not baked into widgets
8. SQLite local; repository is the production swap point (not durable on Vercel)
9. Engine ≠ chatbot
10. Briefing foundation via `IntelligencePipeline.briefing()`

## Files added / changed

- `src/mccc/intelligence/` (schema, services, adapters, pipeline, repository, demo_feed)
- `pages/24_Intelligence_Center.py`
- `src/mccc/db.py` (seed hook), `ui.py` (quick action), `bookmarks.py`, `__init__.py` version
- `docs/INTELLIGENCE_PLAN.md`, `docs/INTELLIGENCE_PHASE1_REPORT.md`
- `tests/test_intelligence_*.py`
- `CHANGELOG.md`, `README.md`

## Tests

- Full suite: **114 passed**
- New coverage: schema/provenance/latency, scoring/source tier, dedupe, classify/normalize, pipeline DEMO seed + idempotent dedupe, summarizer no-hallucination, candidates not auto-verified, ingestion_runs

## Known gaps (P1 out of scope)

- Email / Telegram / Discord alerts
- Continuous cron workers on Vercel
- Live API keys beyond optional public RSS
- Full investor analytics dashboards
- Assistant grounded “while away” briefing UI (foundation only)

## Commit

- SHA: `c4b4cf13bc10d420db1a8aff87c737668c7d6cf1` (`c4b4cf1`)
- Branch: `main` ahead of origin by 1 — **not pushed**
- Tests: **114 passed**
