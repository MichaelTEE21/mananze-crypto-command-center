# MCCC Master Plan — implementation order (keep Streamlit)

**Audience:** engineer picking up after audit (`docs/AUDIT.md`)  
**Rules:** No framework rewrite. Keep Partner Links. Prefer wiring existing `src/mccc/*` services over new abstractions. Nullable `user_id` everywhere so single-operator mode keeps working.

---

## Phase 0 — Foundation bootstrap (½–1 day)

1. **Env load** — call `load_dotenv()` once from a tiny `mccc/bootstrap.py` (or top of `app.py` + `page_setup`) so `.env` matches `.env.example`.
2. **Smoke** — `pytest`; confirm `init_db` creates all tables on a fresh `data/mccc.db`.
3. **README delta** — note v1.1 services, AI_* / AUTH_SECRET env vars, “schema ahead of UI”.

Do not touch Partner Links behaviour except optional `source_page` plumbing later.

---

## Phase 1 — Schema + services complete (1–2 days)

### Already done (verify, don’t redo)

- Tables: users, profiles, portfolio_assets, watchlist_items, alerts, notifications, airdrop_tasks, education_progress, subscriptions, ai_usage, analytics_events  
- Services: `auth`, `portfolio`, `watchlist`, `notifications`, `ai_service`, `market_provider`  
- Migrations: `_migrate_schema` for projects/airdrops/partner clicks  

### Still add (thin CRUD modules)

| New module | Table(s) | API sketch |
|------------|----------|------------|
| `airdrop_tasks.py` | `airdrop_tasks` | add/list/toggle_done/delete by `airdrop_id` |
| `education.py` | `education_progress` | upsert progress, list by user/lesson |
| `subscriptions.py` | `subscriptions` | get_or_create free tier; set_tier local-only; **no payment provider** |

### Hardening

- Dual-write or migrate `log_event` → also `analytics_events` (pick one primary for page 9).
- Ensure `partners.record_click(..., source_page=)` used from `ui.partner_cta`.
- Unit tests mirroring `test_portfolio` / `test_watchlist` for the three new modules.

**Exit criteria:** all command-center tables have a Python service + pytest; no page changes required yet.

---

## Phase 2 — Wire market + portfolio foundation into UI (1–2 days)

1. Switch `app.py`, `5_Market_APIs.py`, `6_Analytics.py` to `get_default_provider()` (TTL cache, overview metrics).
2. Sidebar or hero **LIVE / DEMO** chip from last `is_live`.
3. Hub portfolio: if `portfolio.list_assets()` non-empty → `compute_summary` + price_map; else show empty CTA + keep labelled DEMO sample behind expander (don’t lie).
4. Optional thin **Portfolio** section on hub or new `pages/13_Portfolio.py` (add/edit/CSV) using `portfolio.py` only.

**Exit criteria:** no silent DEMO when live prices exist; portfolio book can be real SQLite rows.

---

## Phase 3 — Upgrade existing tracker pages (2–3 days)

### Project Tracker

- Forms expose `stage` (`PROJECT_STAGES`) + key extended fields (risk, website, docs, next_action, last_checked).
- Keep legacy `status` in sync via existing `update_project` mapping or deprecate gradually.

### Airdrop Tracker

- Status selectbox → `AIRDROP_STATUSES`.
- Extra fields: token, points, claim_page, official_website.
- Embed **task checklist** via new `airdrop_tasks` service.

### Wallet Tracking

- Keep public-address rules.
- Cross-link: adding a wallet can optionally add `watchlist_items` type=`wallet`.

### AI Assistant

- Call `ai_service.answer`; badge `rule_based` / `llm` / `refusal`.
- Keep note structuring; log usage already handled in service.

### Education

- Mark complete → `education_progress`.
- Expand 2–3 longer lessons later (content, not framework).

**Exit criteria:** pages match schema vocabulary; airdrop tasks usable end-to-end.

---

## Phase 4 — New command-center surfaces (2–3 days)

Order matters (dependencies):

1. **Watchlist + Alerts page** — CRUD via `watchlist.py`; show active alerts (no background worker yet).
2. **Notifications** — sidebar unread count + simple inbox page/expander (`notifications.py`).
3. **Auth (optional local)** — sidebar login/register using `auth.py`; store session user; pass `user_id` into portfolio/watchlist when present. Admin Partner page can later accept `is_admin` **or** keep env password (prefer: env password remains for break-glass).
4. **PRO / subscriptions** — `subscriptions.get` drives `is_feature_enabled` optionally; still **no checkout**; keep mock paywall copy.
5. **Alert evaluator (local button or session tick)** — compare watchlist token prices from `market_provider` vs thresholds → create notifications. Label DEMO vs live.

**Exit criteria:** operator can register locally, hold a portfolio, watchlist with alerts, see notifications — all Streamlit.

---

## Phase 5 — UI polish (parallel / ongoing, 1–2 days)

- `st.page_link` nav from hub cards.
- Stronger terminal CSS in `ui.py` (borders, mono KPIs, denser tables).
- Consistent badges: LIVE, DEMO, PRO, REFERRAL.
- Partner CTA: Track & open records `source_page`.

Do **not** restyle Partner Directory into a different IA.

---

## Phase 6 — Tests & docs (1 day, after each phase ideally)

| Layer | Add |
|-------|-----|
| Unit | `test_market_provider` (cache hit, DEMO flag), `test_ai_service` (refusal, rule path), tasks/education/subscriptions |
| Integration | init_db idempotence with full schema; portfolio summary + provider price_map |
| Docs | Update README stage table; keep AUDIT as historical; tick this plan |

CI optional: `pytest` on push when GitHub is requested.

---

## Explicit non-goals (this master upgrade)

- Next.js / React rewrite  
- Real payment processing / Stripe  
- Custodial wallets, seed storage, signing  
- Hosted multi-tenant SaaS hardening (rate limits, CSRF, OAuth) — defer  
- Replacing Partner Links data model  

---

## Suggested calendar (one engineer)

| Week | Focus |
|------|-------|
| Day 1 | Phase 0–1 (bootstrap + missing services + tests) |
| Day 2–3 | Phase 2 (market provider + real portfolio UI) |
| Day 4–5 | Phase 3 (tracker/AI/education wiring) |
| Day 6–7 | Phase 4 (watchlist, notifications, optional auth) |
| Day 8 | Phase 5–6 (polish + test/docs pass) |

Ship incrementally; each phase should leave `pytest` green and DEMO/LIVE labelling intact.
