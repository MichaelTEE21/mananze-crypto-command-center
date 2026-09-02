# MCCC Audit — AUDIT ONLY (no rewrite)

**Audited:** 2026-09-02 (SAST / Africa/Johannesburg)  
**Tree:** `/workspace/mccc` · package `mccc` **v1.1.0-dev**  
**Constraint:** Keep Streamlit; Partner Links already shipped — do not rip out.  
**Method:** Full read of `app.py`, all `pages/*`, `src/mccc/*`, `tests/*`, `README.md`, `.env.example`, `requirements.txt`, education content, Streamlit theme.

---

## 1. Framework — keep Streamlit (justified vs Next.js)

MCCC is a **local research OS**: SQLite on disk, PowerShell/POSIX one-click start, privacy-first (no phone-home), Python-native data (pandas / Plotly / requests), and a single operator (B=MananzeZA) iterating research workflows.

| Criterion | Streamlit (current) | Next.js rewrite |
|-----------|---------------------|----------------|
| Local-first SQLite + Python analytics | Native, zero API layer | Needs Node API / ORM / dual runtime |
| Time-to-upgrade for master plan | Days (pages + services) | Weeks–months (full rewrite) |
| Partner Links + admin CRUD already shipped | Keep as-is | Rebuild |
| Premium dark terminal UX | Achievable with CSS + theme (already started) | Better design control, but wrong cost curve |
| Multi-tenant SaaS / OAuth | Weak | Stronger — **not** the current product goal |

**Verdict:** Keeping Streamlit is correct for this product class. Next.js only becomes rational if the goal shifts to hosted multi-user SaaS with real billing — and even then, a thin FastAPI + Streamlit (or separate web) hybrid beats a greenfield rewrite of working research tools.

---

## 2. Current pages — what each actually does vs mock

| Stage | File | Real (SQLite / live I/O) | DEMO / mock |
|------:|------|--------------------------|-------------|
| 1 | `app.py` | Counts from `projects` / `airdrops` / `wallets` / partners; market snapshot via `fetch_prices` | Portfolio metric + table = **hardcoded `DEMO_PORTFOLIO`** (not `portfolio_assets`) |
| 2 | `2_Project_Tracker.py` | Full CRUD on `projects` | Seed DEMO rows on empty DB; form **does not expose** extended columns (`stage`, risk, funding, TGE, tasks, …) already on schema |
| 3 | `3_Airdrop_Tracker.py` | Full CRUD on `airdrops` | Seed DEMO rows; status selectbox still uses **legacy** labels (`watching`/`eligible`/…) while DB migrates to `AIRDROP_STATUSES`; **no `airdrop_tasks` UI** |
| 4 | `4_Wallet_Tracking.py` | Public address watchlist CRUD; partner Wallet expander; balance lookup | `0xDEMO…` balances; live = Etherscan (if key) or Cloudflare ETH RPC |
| 5 | `5_Market_APIs.py` | CoinGecko `coins/markets` | DEMO fallback table when unreachable; **does not yet call `market_provider`** (TTL cache unused by page) |
| 6 | `6_Analytics.py` | Live or DEMO price bars | Synthetic 30d history + DEMO portfolio pie; PRO panel gated by feature flag |
| 7 | `7_AI_Assistant.py` | Rule tips + `research_notes` save | **Does not call `ai_service.answer`** yet; optional LLM path exists in service only; PRO deep-research is static copy |
| 8 | `8_Education.py` | Renders `content/education/*.md` | No progress tracking (`education_progress` unused) |
| 9 | `9_User_Analytics.py` | Local `usage_events` aggregates | No PII; `analytics_events` table exists but page reads `usage_events` only |
| 10 | `10_PRO_Architecture.py` | Feature flag toggles in SQLite | Paywall UI mock (disabled button); `MCCC_PRO_UNLOCK=1` overrides; **no `subscriptions` wiring** |
| 11 | `11_Partner_Directory.py` | Active links from DB; CTAs; disclosure | DEMO seed partners (`example.com`) labelled |
| 12 | `12_Admin_Partner_Links.py` | CRUD + click analytics | Session unlock via `MCCC_ADMIN_PASSWORD` or DEMO password `mccc-admin-demo` |

**Nav honesty:** Command Center stage cards match the 12 stages. Sidebar is Streamlit multipage (cards are descriptive, not `st.page_link` deep links).

---

## 3. SQLite tables — present vs wired

### Created by `SCHEMA` in `db.py` (and migrations)

**Core (used by pages today)**  
`projects`, `airdrops`, `wallets`, `usage_events`, `feature_flags`, `research_notes`, `partner_links`, `partner_link_clicks`

**Also created (production command-center set)**  
`analytics_events`, `users`, `profiles`, `portfolio_assets`, `watchlist_items`, `alerts`, `notifications`, `airdrop_tasks`, `education_progress`, `subscriptions`, `ai_usage`

**Extended columns (migrated)**  
Projects: description, category, risk_rating, funding, investors, token, tge, website, docs, social_links, tasks, wallet, last_checked, next_action, stage.  
Airdrops: category, dates, token, eligibility, points, rank, wallet_used, URLs.  
Partner clicks: `source_page`.

### Service modules (backend ready; pages mostly not)

| Module | Covers | Page UI? |
|--------|--------|----------|
| `auth.py` | users + profiles, scrypt, session helpers | **No** login/register page |
| `portfolio.py` | portfolio_assets CRUD, PnL, CSV | **No** — hub still DEMO_PORTFOLIO |
| `watchlist.py` | watchlist_items + alerts | **No** (wallet page is separate `wallets` table) |
| `notifications.py` | notifications inbox CRUD | **No** |
| `ai_service.py` | rule/LLM answer + `ai_usage` log | **Not wired** into page 7 |
| `market_provider.py` | CoinGecko + 60s TTL cache + overview | **Not wired** into pages 1/5/6 |
| — | `airdrop_tasks` | **No service, no UI** |
| — | `education_progress` | **No service, no UI** |
| — | `subscriptions` | **No service**; PRO page is flag mock only |

### Gap vs “production command center” checklist

| Desired | Table | Status |
|---------|-------|--------|
| users | `users` (+ `profiles`) | **Schema + auth service**; no UI |
| portfolio_assets | yes | **Schema + portfolio service**; hub still DEMO |
| watchlists | `watchlist_items` | **Schema + service**; no UI (distinct from `wallets`) |
| alerts | `alerts` | **Schema + service**; no evaluator / UI |
| notifications | `notifications` | **Schema + service**; no UI |
| airdrop_tasks | yes | **Schema only** |
| education_progress | yes | **Schema only** |
| subscriptions | yes | **Schema only** (provider=`coming_soon`) |
| ai_usage | yes | **Schema + ai_service logging**; page still rule-only |

---

## 4. APIs, caching, demo-vs-live honesty

### External APIs

| Source | Where | Behaviour |
|--------|-------|-----------|
| CoinGecko `/coins/markets` | `market.py` / `market_provider.py` | Live when reachable; else DEMO table |
| CoinGecko `/global` | `market_provider.get_overview` | Live dominance/mcap when reachable |
| Etherscan balance | `wallets.py` | Only if `ETHERSCAN_API_KEY` set |
| Cloudflare ETH RPC | `wallets.py` | Public `eth_getBalance` fallback |
| OpenAI-compatible chat | `ai_service.py` | Only if `AI_API_KEY` set |

### Caching

- **`market_provider.CoinGeckoProvider`**: in-process TTL cache (~60s) for prices + overview — **good**.
- **Pages still call `market.fetch_prices` directly** → cache bypassed until pages switch provider.
- **No Streamlit `@st.cache_data`** anywhere.
- **`python-dotenv` is listed but `load_dotenv()` is never called** → `.env` keys often never load unless the shell exports them (`START.ps1` does not `dotenv` either).

### Labelling honesty — strong, with one hub inconsistency

**Strong**

- `DEMO_BANNER`, `demo_callout`, success/info source strings on market pages.
- Wallet balances carry `source` / `is_live`.
- Partner DEMO rows use `example.com` + DEMO in name/description.
- Assistant / `ai_service` refuse inventing live prices; portfolio valuation leaves missing prices as `None`.
- PRO paywall explicitly “not charged”.

**Gap**

- Command Center portfolio card is always DEMO while adjacent market snapshot may be LIVE — correct labels exist, but **no path to replace DEMO portfolio with `portfolio_assets` yet**, so the hub teaches the wrong mental model for “my book”.

---

## 5. Auth

| Layer | Reality |
|-------|---------|
| App-wide gate | **None** — all research pages open locally |
| Partner admin | **Password only** (`MCCC_ADMIN_PASSWORD` or DEMO `mccc-admin-demo`), session flag `mccc_admin_unlocked` |
| User accounts | `auth.register_user` / `login` with **stdlib scrypt**; Streamlit session helpers; **no page** |
| PRO | Feature flags + env unlock — not identity-based |

**Honest summary:** Today = local single-operator + admin password for partner CRUD. Multi-user auth is **scaffolded**, not productized.

---

## 6. Security (seeds / keys / secrets)

**Keep / good**

- Wallet + DB `add_wallet` reject seed/mnemonic/private markers; DEMO `0xDEMO…` allowed.
- Partner pages show `SEED_PHRASE_WARNING`; tests smoke-check pages don’t solicit keys.
- `auth` / `ai_service` refuse secret-looking input.
- `.gitignore` covers `.env`, `*.db`, `*.pem`, `*.key`, `.streamlit/secrets.toml`.
- Partner click analytics: link id + category + timestamp (+ optional `source_page`) — **no IP / UA**.
- Streamlit `gatherUsageStats = false`.

**Improve**

1. Call `load_dotenv()` once at startup (`app.py` / shared bootstrap) so `.env.example` is truthful.
2. DEMO admin password is fine locally but must stay labelled; refuse shipping with that default in any hosted mode.
3. `users.password_hash` is appropriate for app login — never confuse with chain keys; keep refusal copy everywhere passwords are collected.
4. Optional LLM: keys only via env; never log prompts that contain secrets (refusal path already short-circuits).

---

## 7. Partner Links — KEEP (shipped)

Central `partners.py` + pages 11/12 are production-quality for this OS:

- Categories Wallet / CEX / DEX / Crypto Tool / Partner  
- Official vs referral resolution; affiliate disclosure; Active-only public directory  
- Admin CRUD, enable/disable/delete, click analytics  
- Seed DEMO partners idempotent; CoinGecko official entry with empty referral  
- Wallet Tracking embeds Active Wallet partners via shared CTA helper  

**Do not rewrite.** Incremental only: pass `source_page` from `partner_cta`, richer admin charts, logo polish.

---

## 8. UI/UX gaps vs premium dark terminal

**Already there**

- Dark theme in `.streamlit/config.toml` (teal `#00d4aa`, `#0b0f14` bg).
- Shared `ui.py`: IBM Plex + JetBrains Mono, hero, cards, badges, sidebar caption.

**Gaps**

- Forms are stock Streamlit — dense tables, weak “terminal” density (no command palette, no sticky KPI strip).
- Inconsistent status vocabularies (legacy page selectboxes vs `PROJECT_STAGES` / `AIRDROP_STATUSES`).
- No global LIVE/DEMO chip in sidebar reflecting last market fetch.
- No notification bell / unread badge despite `notifications` service.
- Education content is short (~66 lines total) — thin for an “OS”.
- Hub navigation cards aren’t clickable `st.page_link`s.
- PRO purple accents exist; rest of app still “dashboard grey” more than CRT/terminal.

---

## 9. Recommended KEEP / IMPROVE / ADD (prioritized, no-rewrite)

### KEEP

1. Streamlit + multipage layout + START scripts  
2. Partner Links stack (`partners.py`, pages 11–12, disclosures)  
3. Seed/key refusal + DEMO labelling conventions  
4. SQLite local store + idempotent seeds + `_migrate_schema`  
5. Existing working CRUD pages (projects, airdrops, wallets)  
6. New services: `auth`, `portfolio`, `watchlist`, `notifications`, `ai_service`, `market_provider`  
7. pytest suite expansion pattern (`test_auth`, `test_portfolio`, …)

### IMPROVE (P0–P1)

| Pri | Item |
|----:|------|
| P0 | Bootstrap `load_dotenv()`; document env in README |
| P0 | Wire Market pages + hub to `market_provider` (TTL + overview) with LIVE/DEMO chip |
| P0 | Replace hub DEMO portfolio with `portfolio` service + honest empty state |
| P0 | Align Project/Airdrop page forms to extended schema + stage/status constants |
| P1 | Wire page 7 to `ai_service.answer` (rule default; LLM optional; show mode badge) |
| P1 | Pass `source_page` into `record_click` from `partner_cta` |
| P1 | Unify usage: either dual-write `analytics_events` or deprecate one table |
| P1 | Darker terminal CSS polish (monospace metrics, denser cards, page_link nav) |
| P2 | Expand education modules; richer Plotly on live series when `is_live` |

### ADD (P0–P2) — wire tables already in schema

| Pri | Item |
|----:|------|
| P0 | Portfolio page (or hub section) + CSV import/export using `portfolio.py` |
| P0 | Watchlist + alerts page using `watchlist.py` (token/project/wallet refs) |
| P1 | Optional local Login/Register sidebar using `auth.py` (single-user still OK with nullable `user_id`) |
| P1 | Notifications inbox strip + `unread_count` in sidebar |
| P1 | `airdrop_tasks` service + checklist UI on Airdrop Tracker |
| P2 | `education_progress` mark-complete / quiz stub |
| P2 | `subscriptions` read-model tied to PRO flags (`coming_soon` provider — still no payments) |
| P2 | Lightweight alert evaluator (price vs threshold → `notifications`) — local only |

---

## Tests snapshot

Present: `test_db`, `test_helpers`, `test_partners`, `test_auth`, `test_portfolio`, `test_watchlist`, `test_notifications`.  
Missing for master upgrade: market_provider cache tests, ai_service refusal/LLM-off path, airdrop_tasks / education_progress once added, page-level smoke (optional).

---

## Bottom line

MCCC is a **credible Stage-1 Streamlit research OS** with **excellent honesty/security posture** and a **shipped Partner Links subsystem**. The master upgrade should **not rewrite**: the schema and many services for a command center are already landing — the debt is **wiring pages**, fixing **dotenv/cache**, and converting **DEMO hub portfolio / thin trackers** into the real tables without abandoning Streamlit.


---

## Post-upgrade note (2026-09-02 · v1.2.0-dev UI)

UI upgrade shipped on top of this audit: pages now wire `market_provider`, `portfolio`, `watchlist`, `notifications`, `auth`, `ai_service`; new thin modules `education`, `airdrop_tasks`, `subscriptions`. Partner Links retained. Streamlit justified verdict unchanged — see `docs/DELIVERABLE.md` and `docs/MASTER_PLAN.md`.
