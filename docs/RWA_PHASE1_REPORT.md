# MCCC RWA Intelligence — Phase 1 Report

## Outcome

RWA (Real-World Assets) intelligence vertical shipped **inside MCCC only** on top of Intelligence Agent Phase 1. Version **2.2.0**. **Not pushed** (parent / ENELO handles push).

## How to run

```bash
cd /workspace/mccc
.venv/bin/python -m streamlit run app.py
# sidebar → RWA Intelligence
.venv/bin/pytest -q
```

## Deliverables status

| Item | Status |
|------|--------|
| Taxonomy (top-level + extensible sub-categories) | Done |
| Schema / models (`rwa_profiles`, links, provenance, asset value types) | Done |
| Intelligence Agent extension (classify + store + DEMO docs) | Done |
| UI — RWA Intelligence Center + filters + cards | Done |
| Dashboard analytics from stored data | Done |
| Global Search RWA-aware | Done |
| RWA watchlist | Done |
| Education foundation modules | Done |
| Risk framework (disclosure indicators) | Done |
| Narrative engine from observed categories | Done |
| DEMO/SYNTHETIC seeds labelled | Done |
| Docs `RWA_PLAN.md` + this report | Done |
| Tests (§23 coverage) | Done |
| Technocore untouched | Confirmed |

## Categories registered

See `all_rwa_categories()` — includes Tokenized Treasuries, Real Estate, Private Credit, Commodities, Agriculture, Infrastructure, Tokenization Platforms, Custody/Settlement, Compliance/Identity, and the full Phase 1 list. New categories via `register_category` without schema rewrite.

## Intelligence integration

- `EventCategory.RWA = "rwa"`
- `ClassificationService` + `RWAClassificationService` detect membership / subcategory / event type
- Pipeline STORE links profiles via `RWAService.upsert_from_event`
- Demo adapter merges RWA DEMO raw docs (example.com only)
- `init_db` seeds RWA DEMO profiles idempotently

## Dashboard / search / education

- Analytics page shows stored RWA category bar chart (DEMO labelled)
- Search categories: `rwa`, `intelligence`
- Education: `rwa_tokenization`, `rwa_treasuries`, `rwa_private_credit`, `rwa_real_estate`, `rwa_custody`, `rwa_collateral`, `rwa_redemption`, `rwa_settlement`, `rwa_risks`

## Demo / live

- All seeds set `is_demo=True`, titles/tags include DEMO/SYNTHETIC
- Asset value estimates labelled **Calculated estimate (not TVL)**; stale timestamps flagged
- Missing fields: Unknown / Not disclosed / Unconfirmed
- No fabricated verified funding or regulatory approvals

## Phase 2 remaining

- Live official issuer / regulatory feed adapters
- NAV / attestation ingestion with stronger provenance UI
- Alerting for RWA watchlist
- Research timeline deep-links per profile
- Optional production Postgres behind same repository interface

## Production blockers

- Local SQLite is **not** durable on ephemeral hosts (same honesty as Intelligence Agent)
- No continuous cron on Vercel assumed — use `ingestion_runs` + manual/scheduled refresh
- Live RSS soft-fails offline; RWA live providers not wired in P1

## Commit

- SHA: `b948fad` (b948fadc64130e1a841b5e40becab49bc33a1b12)
- Branch: `main` ahead of origin — **not pushed**
- Tests: **132 passed**
