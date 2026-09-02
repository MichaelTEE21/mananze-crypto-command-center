# MCCC RWA Intelligence — Plan (Phase 1)

**Product:** MANANZE CRYPTO COMMAND CENTER (MCCC)  
**Vertical:** RWA — REAL-WORLD ASSETS  
**Base:** Intelligence Agent Phase 1 (`08d1882` / v2.1.0)  
**Rule:** MCCC only — never touch Technocore. Education + disclosure framework — not trading, custody, or buy/sell ratings.

## Goals

Ship a first-class RWA intelligence vertical that:

1. Extends existing Intelligence Agent tables/relationships (Project → RWA Profile → Events → Funding → Sources → Watchlist → Research)
2. Never fabricates funding, TVL, investors, regulatory approvals, or TGE dates
3. Labels DEMO/SYNTHETIC clearly; caches ingestion results
4. Uses disclosure indicators (DISCLOSED / NOT DISCLOSED / UNKNOWN) — not investment advice

## Taxonomy

**Top-level:** `RWA — REAL-WORLD ASSETS` across Intelligence Center, Project Tracker, Global Search, Research, Narratives, Watchlists, Education, Analytics.

**Sub-categories (extensible, no schema rewrite):** Tokenized Treasuries, Real Estate, Private Credit, Corporate Credit, Consumer Credit, Commodities, Gold/Precious Metals, Agriculture, Trade Finance, Infrastructure, Energy, Funds, Securities, Bonds, Stablecoins, Carbon/Environmental, Collectibles/Art, Insurance-linked, RWA Infrastructure, Tokenization Platforms, Custody/Settlement Infrastructure, Compliance/Identity Infrastructure.

**Event types:** NEW_PROJECT, ASSET_LAUNCH, FUNDING, PARTNERSHIP, TOKEN_LAUNCH, CHAIN_LAUNCH, INSTITUTIONAL_ADOPTION, REGULATORY, CUSTODY, SETTLEMENT, COLLATERAL, REDEMPTION, INTEGRATION, ACQUISITION, MAINNET, TESTNET, OTHER (+ `register_event_type`).

## Schema

- `rwa_profiles` — directory fields + verification DISCOVERED|REVIEW|VERIFIED|TRACKING|ARCHIVED
- `rwa_profile_events` — link to `intelligence_events`
- `rwa_watchlist` — project / category / chain / narrative / profile
- Asset value types: verified reported | calculated estimate (never “TVL”) | unavailable + measurement timestamp (stale flagged)
- Provenance tiers: Official issuer → Docs → Regulatory/institutional → Established publication → Secondary → Social
- Funding links to existing `funding_rounds` via `funding_round_id` — no invented rounds

## Pipeline

Same Intelligence Agent order: INGEST → NORMALIZE → DEDUPE → CLASSIFY → EXTRACT → SCORE → SUMMARIZE → STORE → DISPLAY.  
CLASSIFY detects RWA membership + subcategory + event type; STORE upserts/links `rwa_profiles`.

## UI (Phase 1)

- `pages/25_RWA_Intelligence.py` — Breaking | New Projects | Tokenized Treasuries | Real Estate | Private Credit | Commodities | Agriculture | Infrastructure | Funding | Institutional | Regulatory | Trends + filters
- Dashboard analytics from stored data only
- Project cards: VIEW / OPEN WEBSITE/DOCS / WATCHLIST / ADD TO PROJECT / VIEW INTELLIGENCE
- Global Search category `rwa` + `intelligence`
- Education modules under `content/education/rwa_*.md`
- Risk framework: disclosure indicators only

## Out of scope (Phase 1)

- Live institutional APIs / paid data vendors
- Trading, custody, investment execution, DEX
- Continuous workers on Vercel
- Auto-VERIFIED promotion
- Fabricated “live” TVL feeds

## Phase 2 (documented only)

- Richer live RWA providers (official issuer feeds)
- Attestation / NAV timestamp pipelines with provenance
- Cross-link Research workspace timelines per profile
- Email/Telegram alerts for watched RWA categories
- Deeper regulatory filing parsers (respect ToS)
