# MCCC 2.0 Audit (Phase 0)

**Audited:** 2026-09-02 (Africa/Johannesburg)  
**Tree:** `/workspace/mccc` · package was **v1.2.0-dev** → Phase 1 bumps to **2.0.0-dev**  
**Rules:** Keep Streamlit. Do not delete Partner Links, portfolio, watchlist, auth, market_provider. Never store seeds/keys. DEMO vs LIVE must stay honest. `official_url` vs `referral_url` — never hardcode referrals.

---

## 1. Current architecture

| Layer | Location | Role |
|-------|----------|------|
| Entry | `app.py` | Command Center cockpit (markets, portfolio summary, research snapshots, quick links) |
| Pages | `pages/1_*` … `18_*` | Multipage Streamlit surfaces (Markets → Search) |
| Package | `src/mccc/` | DB, auth, partners, portfolio, watchlist, notifications, market*, AI*, education, UI |
| Content | `content/education/*.md` | Local education modules |
| Data | `data/` (SQLite via `paths.DB_PATH`) | Local-only persistence |
| Config | `.env.example`, `.streamlit/config.toml` | Optional API keys; dark theme |
| Launch | `START.ps1` / `START.bat` | Windows-friendly venv + streamlit |
| Tests | `tests/` | pytest unit coverage |

**Stack:** Streamlit 1.39 + pandas/plotly + requests + python-dotenv + SQLite.

**Honesty model:** Providers return `(data, source_label, is_live)`. DEMO fallbacks are labelled. Portfolio never invents missing prices.

**Partner model:** `partner_links.official_url` + optional `referral_url`; `resolve_visit_url` prefers referral only when non-empty. Admin CRUD on page 12.

---

## 2. KEEP / IMPROVE / ADD

### KEEP (do not rip out)

1. Streamlit multipage + START scripts  
2. Partner Links (`partners.py`, pages 11–12, disclosures, click analytics)  
3. Seed/key refusal culture + DEMO labelling  
4. SQLite + `_ensure_column` / `_migrate_schema` (never wipe)  
5. Working CRUD: projects, airdrops, wallets  
6. Services already present in v1.2: `auth`, `portfolio`, `watchlist`, `notifications`, `ai_service`, `market_provider`, `airdrop_tasks`, `education`, `subscriptions`  
7. Pages 13–18 (Portfolio, Watchlist, Notifications, Account, Start Here, Search)  
8. pytest suite pattern  

### IMPROVE

| Area | Gap |
|------|-----|
| Security | Scattered markers in auth/wallets/ai — centralize (Phase 1: `security.py`) |
| Architecture | Flat `src/mccc/*` — add `services/` facades without breaking imports |
| Schema | Missing exchanges/resources/announcements/bookmarks/research_events/project_tags/settings |
| research_notes | No `project_id` link / timeline |
| Env | `load_dotenv` was only in `ui.py` — also call from `app.py` |
| Trackers | Some extended project/airdrop columns underused in forms |
| Alert evaluator | Alerts table exists; no local price→notification evaluator yet |
| Education | Progress service exists; content depth uneven |
| Analytics | Both `usage_events` and `analytics_events` — unify later |

### ADD (2.0 roadmap — see PLAN)

- Dedicated `exchanges` table (admin-managed; optional sync from CEX/DEX partners)  
- Resources, bookmarks, announcements, research timeline, project tags, app_settings  
- Stronger automated credential-rejection tests  
- Future UI for exchanges/resources/bookmarks (Phases 2+)  

---

## 3. Security risks

| Risk | Status |
|------|--------|
| Seed / mnemonic / privkey paste into wallet or forms | Mitigated: validation + Phase 1 central `reject_sensitive_credential`; tests expanded |
| App login password confused with chain keys | Mitigated: copy + refusal markers; scrypt hash only for app users |
| Hardcoded referral URLs | Mitigated: DB fields only; never hardcode in code |
| DEMO presented as LIVE | Mitigated: badges + source strings; keep discipline in new pages |
| `MCCC_ADMIN_PASSWORD` DEMO default | Acceptable local-only; never ship hosted with default |
| LLM prompt leaking secrets | `ai_service.contains_secrets` refusal path; Phase 1 routes through security |
| `.env` secrets in git | `.gitignore` covers `.env`, `*.db`, keys |

**Non-negotiable:** Never accept/store seed phrases, private keys, exchange/wallet passwords, 2FA secrets.

---

## 4. Dead / thin code (not deleted)

| Item | Notes |
|------|-------|
| `market.py` | Legacy `fetch_prices`; still used by provider / tests — keep as thin helper |
| `assistant.py` | Rule tips; AI page prefers `ai_service` — keep |
| Dual usage tables | `usage_events` vs `analytics_events` — consolidate later, don’t drop |
| Feature flags vs subscriptions | Both gate PRO; document which wins (`MCCC_PRO_UNLOCK` overrides) |
| Empty `exchanges` until Phase 2 UI | Table created Phase 1; no seed wipe of partners |

---

## 5. Pages inventory (v1.2 on disk)

| Page | Wired to real data? |
|------|---------------------|
| Command Center (`app.py`) | Yes — provider + portfolio + counts |
| Markets / Market APIs / Analytics | Provider + LIVE/DEMO |
| Project / Airdrop / Wallet trackers | SQLite CRUD |
| AI Assistant | `ai_service.answer` |
| Education | Markdown + progress helpers |
| User Analytics | Local usage events |
| PRO Architecture | Flags / subscriptions mock — no payments |
| Partner Directory + Admin | Full |
| Portfolio / Watchlist / Notifications / Account | Services wired |
| Start Here / Search | Onboarding + local search |

---

## 6. Env vars required / optional

See `.env.example`. Phase 1 does not add new required vars.

| Var | Required? | Purpose |
|-----|-----------|---------|
| `COINGECKO_API_KEY` | Optional | Higher CoinGecko limits |
| `ETHERSCAN_API_KEY` | Optional | Wallet balance via Etherscan |
| `MCCC_PRO_UNLOCK` | Optional | Local PRO UI unlock (`0`/`1`) |
| `MCCC_ADMIN_PASSWORD` | Optional | Partner admin gate (DEMO default if unset) |
| `AI_API_KEY` / `AI_API_BASE` / `AI_MODEL` | Optional | LLM assistant |
| `AUTH_SECRET` | Optional | Session salt |
| `DATABASE_URL` | Ignored | SQLite path is local |

---

## 7. Bottom line

v1.2 is a **credible local research OS** with Partner Links and command-center services already landing. MCCC 2.0 should **extend schema + harden security + add facades**, then ship new surfaces (exchanges, resources, bookmarks, research timeline) **without rewriting Streamlit or deleting working features**.
