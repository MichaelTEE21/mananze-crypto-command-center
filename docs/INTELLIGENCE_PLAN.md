# MCCC Intelligence Agent — Plan (Phase 0 audit + phased delivery)

**Product:** MANANZE CRYPTO COMMAND CENTER (MCCC)  
**User:** B=MananzeZA  
**Base:** MCCC 2.0.0 (`b42e2de`)  
**Rule:** Intelligence engine ≠ chatbot. Engine discovers/structures first; assistant explains second.

## Phase 0 — Existing MCCC map

| Area | Entry / module | Notes |
|------|----------------|-------|
| App entry | `app.py` | Command Center cockpit; markets LIVE/DEMO |
| Nav / pages | `pages/1_*` … `pages/23_*` | Streamlit multipage |
| DB | `src/mccc/db.py` | SQLite `data/mccc.db`; `init_db` + migrations |
| Projects | `db.add_project` / Project Tracker | Stages DISCOVERED→… |
| Airdrops | Airdrop Tracker + `airdrop_tasks` | Soft FREE limits |
| Research | `pages/21_Research.py`, `research.py` | Notes + timeline |
| Bookmarks | `bookmarks.py` | Favourites by item_type |
| Education | `education.py` + `content/education/` | Local markdown |
| AI assistant | `pages/7_AI_Assistant.py`, `ai_service` | Rule-based default; optional LLM |
| Analytics | `pages/6_*`, `9_*` | Usage / user analytics |
| Admin | `pages/22_Admin.py` | Admin password / is_admin |
| Auth | `auth.py` | scrypt; guest OK |
| Watchlist (market) | `watchlist.py` / page 14 | Tokens etc. — separate from intel watchlist |
| Design system | `ui.py` | Dark MCCC 2.0 cards/badges |

**Security invariants:** never store/request seeds, private keys, wallet passwords, 2FA.

## Non-negotiables (Phase 1)

1. **Schema first** — `intelligence_events`, `intelligence_sources`, candidate projects (`intelligence_candidates` + link to existing `projects`), `funding_rounds`, `narratives`, `intelligence_watchlist`, `ingestion_runs`; expose `discovery_latency = discovered_at - published_at`.
2. **Pipeline order** — INGEST → NORMALIZE → DEDUPE → CLASSIFY → EXTRACT → SCORE → SUMMARIZE → STORE (filter before expensive summarize).
3. **No fabricated intelligence** — Unknown / Not disclosed / Unconfirmed; never invent funding, investors, TGE, airdrops, prices.
4. **DEMO/LIVE separation** — every synthetic row visibly DEMO/SYNTHETIC; never mix without labels.
5. **UI sections** — Breaking | New Projects | Funding | Airdrop Signals | Token Events | Trending Narratives | Watchlist.
6. **Provenance minimum** — `source_url`, `source_type`, `published_at`, `discovered_at`, `confidence`, `importance`.
7. **Provider interfaces** — RSS / official feeds / stubs; DEMO via seed fixtures, not hard-coded into UI widgets.
8. **Persistence** — SQLite OK locally; repository swappable; do not pretend local FS is durable on Vercel.
9. **Engine ≠ chatbot** — Intelligence Center is not chat-only; assistant may sit on top of the intel DB later.
10. **Goal** — foundation for “What happened in crypto while I was away?” ranked briefing from sourced events.

## What ships in Phase 1 (this turn)

- Modular services: Source, Ingestion, Normalization, Deduplication, Classification, Extraction, Scoring, Summarization, IntelligenceRepository, Pipeline
- Enums: SourceTier 1–5, categories, confidence, airdrop signal statuses, importance bands
- Event schema + funding + candidates (DISCOVERED→REVIEW→VERIFIED→TRACKING; no auto-verify)
- Ingestion run state for cron architecture (no continuous Vercel workers assumed)
- DEMO seed fixtures + optional live RSS soft-fail
- Streamlit page `pages/24_Intelligence_Center.py`
- Tests: schema, scoring, dedupe, source tier, pipeline filter, no-hallucination summarizer
- Docs: this plan + `INTELLIGENCE_PHASE1_REPORT.md`

## Later phases (document only in P1)

| Phase | Scope |
|-------|--------|
| P2 | Richer live providers (official APIs), narrative heat scoring, briefing digest UI |
| P3 | Email / Telegram / Discord alerts |
| P4 | Investor analytics dashboards |
| P5 | Continuous scheduled workers (self-hosted cron / worker — not Vercel 1-min) |
| P6 | Assistant grounded answers over intel DB (“while I was away” briefing) |

## Integration points

- `init_db` → `IntelligencePipeline.seed_demo_if_empty()`
- Bookmarks `intelligence_event` / `narrative`
- “Add to Project” → existing `projects` as DISCOVERED
- Quick action link to Intelligence Center
- Future: `ai_service` reads `IntelligenceRepository.briefing()` — not implemented as chat-only in P1

## Robots / ToS stance

Prefer public RSS / official feeds; respect rate limits; soft-fail; no aggressive HTML scraping or paywall bypass. See `ROBOTS_TOS_STANCE` in `source_service.py`.
