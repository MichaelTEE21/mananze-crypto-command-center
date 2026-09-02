# Changelog

## 2.1.0 — Intelligence Agent Phase 1

- Add MCCC Intelligence Agent foundation (engine ≠ chatbot): modular pipeline INGEST→NORMALIZE→DEDUPE→CLASSIFY→EXTRACT→SCORE→SUMMARIZE→STORE
- Tables: intelligence_events, intelligence_sources, funding_rounds, intelligence_candidates, narratives, intelligence_watchlist, ingestion_runs
- Intelligence Center page with Breaking / New Projects / Funding / Airdrop Signals / Token Events / Narratives / Watchlist
- DEMO/SYNTHETIC seed fixtures clearly labelled; optional live RSS soft-fail; no fabricated funding/investors/TGEs
- Repository layer over SQLite (local); production-swappable — not claimed durable on Vercel



All notable changes to MANANZE CRYPTO COMMAND CENTER (MCCC) are documented here.

## 2.0.0 — Release (2026-09-02)

### Added
- **Phase 12 Auth polish:** Account register/login/logout, profile edit, onboarding goals/experience, password change (scrypt), soft-delete account cascade; session helpers documented; `MCCC_BOOTSTRAP_ADMIN_EMAIL` / `app_settings.bootstrap_admin_email` for first admin
- **Phase 13 PRO gating:** FREE soft limits (projects/wallets/airdrops), upgrade CTA, `has_pro_feature` + `MCCC_PRO_UNLOCK`; PRO page $4/mo Coming Soon — **"PRO payments are not yet enabled."** (never fake success); advanced analytics CSV export + alerts/deep-research gates
- **Phase 14 Production hardening:** version **2.0.0**; README rewrite; `pages/23_Diagnostics.py` (`MCCC_DEV=1`) + Admin Diagnostics tab; `config.validate_config` warn-only; footer version on all pages; DELIVERABLE + `docs/MCCC20_SHIP.md`
- `src/mccc/config.py` — optional env validation (no crash, no secret echo)

### Changed
- Soft gates on Project / Airdrop / Wallet add forms
- `.env.example` documents bootstrap, dev, free-limit overrides

### Security
- Soft-delete scrubs password hash; credential refusal on password change / profile / onboarding
- Diagnostics never displays API key values

### Kept
- Partner Links model, DEMO/LIVE honesty, seed/key refusal, START.ps1 / START.bat + load_dotenv

### Tests
- `tests/test_phase12_14.py` — auth, limits, bootstrap, config, version, security regression

## 2.0.0-dev — Phase 7–11 Education / Search / AI / Analytics / Admin (2026-09-02)

### Added
- Phase 7 Education platform: BEGINNER / INTERMEDIATE / ADVANCED catalog (`education.py` metadata + frontmatter), quizzes, glossary, related lessons, honest progress counts
- Intermediate/advanced lessons: bridges, staking, L1/L2, MEV, DePIN, ZK basics, AI agents; expanded DeFi
- Phase 8 Search helpers (`search.py`) + upgraded Search page (category filters, session recent searches) covering projects/airdrops/wallets/exchanges/education/resources/notes
- Bookmarks section on Watchlist; `bookmarks.list_bookmarks` / delete; Research workspace `pages/21_Research.py`
- Phase 9 `AssistantProvider` abstraction (rule + OpenAI-compatible) in `ai_service` / `services/ai.py`; market questions use `market_provider`; research checklist UI; ai_usage logging retained
- Phase 10 User Analytics: partner referral clicks, lesson completions, resource click sums, privacy note
- Phase 11 Admin panel `pages/22_Admin.py` (password / is_admin): announcements CRUD publish/expire, featured settings, resources CRUD, feature flags, exchange seed, subscription Coming Soon; links to Partner + Exchange admin
- `src/mccc/resources.py` CRUD + click_count

### Kept
- Partner Links model, DEMO/LIVE honesty, seed/private-key refusal, official_url ≠ referral_url

### Tests
- `tests/test_phase7_11.py` — education categories, resources, search, announcements, AI provider, bookmarks

## 2.0.0-dev — Phase 4–6 Project / Airdrop / Directories (2026-09-02)

### Added
- Phase 4 Project Tracker: product stages (DISCOVERED→ARCHIVED), rich create/edit fields, kanban + filters/sort/favourites, research_events timeline, project_tags, credential rejection on notes
- Phase 5 Airdrop Tracker: product statuses (DISCOVERED→ARCHIVED), dashboard (active/deadlines/completed/missed/priority), richer fields + task checklist
- Phase 6 Wallet Directory (`pages/19_Wallet_Directory.py`) — educational + Partner Wallet category; Learn Before You Connect
- Phase 6 Exchange Directory (`pages/20_Exchange_Directory.py`) — `exchanges` CRUD UI, DEMO seed rows, official vs referral, Track & open, admin gate
- Modules: `research.py`, `bookmarks.py`, `exchanges.py` (seed_demo_exchanges + resolve_visit_url)

### Changed
- Legacy stage/status strings migrate to canonical product vocabulary (aliases preserved)
- Command Center active-stage sets aligned with Phase 4–5
- Wallet Tracking warnings strengthened; links to Wallet Directory + Education

### Kept
- Partner Links, DEMO/LIVE honesty, never accept seeds/keys, official_url ≠ referral_url

### Tests
- `tests/test_exchanges_research.py` — exchanges CRUD, research events security, bookmarks, stage maps

## 2.0.0-dev — Phase 2 Design System + Phase 3 Command Center (2026-09-02)

### Added
- Design system upgrades in `src/mccc/ui.py`: denser dark-terminal CSS, status colors (success/warn/danger/info), table/sidebar/mobile polish
- UI helpers: `status_badge` / `status_badge_html`, `section_header`, enhanced `metric_card` (delta), `data_mode_chip`, `footer` (version), `quick_actions`
- `src/mccc/announcements.py` — thin `list_published` (+ minimal `create` for tests)
- Command Center cockpit (`app.py`): market snapshot LIVE/DEMO, active projects/upcoming stages, airdrop deadlines, wallets/watchlist, portfolio, unread notifications, announcements, research activity, quick actions, security + affiliate disclosure

### Kept
- Partner Links model, DEMO/LIVE honesty, seed/private-key refusal

### Tests
- `tests/test_ui_helpers.py` for pure badge/chip HTML + published announcements filter

## 2.0.0-dev — Phase 1 Architecture Cleanup (2026-09-02)

### Added
- `src/mccc/security.py` — central `reject_sensitive_credential()` / mnemonic & hex-key detection; used by wallets, auth, AI paths.
- `src/mccc/services/` — thin facades (`market`, `ai`) re-exporting existing modules; legacy imports unchanged.
- Schema (CREATE IF NOT EXISTS + migrations, no data wipe):
  - `exchanges` (official_url vs referral_url; CEX|DEX; Active|Disabled)
  - `resources`, `announcements`, `bookmarks`
  - `research_events`, `project_tags`
  - `app_settings` key/value
  - `research_notes.project_id` column
- Settings helpers: `get_setting` / `set_setting` / `list_settings`
- Expanded automated security rejection tests (`tests/test_security.py`)
- Docs: `docs/MCCC20_AUDIT.md`, `docs/MCCC20_PLAN.md`

### Changed
- Version bumped to **2.0.0-dev**
- `load_dotenv()` at `app.py` startup (also already in `ui.page_setup` path)
- `db.add_wallet`, `wallets.validate_public_address`, `auth._refuse_secrets`, `ai_service.contains_secrets` route through security helpers

### Security
- Never accept/store seed phrases, private keys, wallet/exchange passwords, or 2FA secrets
- DEMO vs LIVE labelling unchanged and honest
- Partner/exchange links keep separate `official_url` vs `referral_url` (never hardcode referrals)

### Kept
- Partner Links, portfolio, watchlist, auth, market_provider, START.ps1/START.bat, all v1.2 pages

## 1.2.0-dev

- UI upgrade: market_provider, portfolio, watchlist, notifications, auth, AI wiring; Partner Links retained.
