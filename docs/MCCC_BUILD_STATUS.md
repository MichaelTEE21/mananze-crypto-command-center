# MCCC Build Status (real inspection)

**Date:** 2026-09-02 (Africa/Johannesburg)  
**Repo:** `MichaelTEE21/mananze-crypto-command-center`  
**Local HEAD at audit start:** `fad774d` — *fix: replace invalid Streamlit sidebar icon ⬡ with 🏠* (confirmed on `main`; `ui.py` uses 🏠)  
**Architecture:** Streamlit 1.39 multipage (`app.py` + `pages/*`), Python package `src/mccc/`, SQLite (`data/mccc.db` / `MCCC_DATA_DIR`)  
**PRIMARY production:** Render service `srv-dabgrrp5efls73anlhe0` → https://mananze-crypto-command-center.onrender.com  
**Out of scope:** Technocore. No Next.js rewrite. Do not create new Render services.

---

## Architecture (as-is)

| Layer | Reality |
|-------|---------|
| UI | Streamlit pages 1–27 + Command Center `app.py`; CSS/helpers in `ui.py` |
| Persistence | SQLite only (`db.py`); `DATABASE_URL` reserved/ignored with warning |
| Markets | `market_provider` → CoinGecko when reachable; DEMO labelled otherwise |
| Intelligence | Event pipeline + Intelligence Report engine + RWA vertical |
| Auth | Local scrypt accounts; guest mode; soft PRO flags (no Stripe) |
| Secrets policy | `security.py` rejects seeds / privkeys / wallet passwords |
| Deploy | Docker + `scripts/start.sh`; health `/_stcore/health`; disk `/data` on PRIMARY |

---

## Working (preserve)

- Command Center cockpit, universal search → ANALYSE → Intelligence Report  
- Markets / Market APIs (LIVE/DEMO chips)  
- Project Tracker, Airdrop Tracker, Wallet Tracking (public addresses only)  
- Portfolio, Watchlist, Notifications  
- Education + quizzes, Start Here onboarding  
- AI Assistant (rule-based + optional LLM); refuses secrets  
- Partner / Exchange / Wallet directories; Admin Partner Links  
- Account register/login/logout/profile/password/delete; PRO Architecture soft gates  
- Intelligence Center + Intelligence Reports; RWA Intelligence  
- Tokens (market foundation; holders/locks UNAVAILABLE); Calendar (schema + DEMO seeds)  
- Search / Research / Bookmarks / Diagnostics (`MCCC_DEV`)  
- Icon fix `fad774d` (🏠) on local main  

## Broken / fragile

- Local `main` was **14 commits ahead of `origin/main`** at audit — production may lag until ENELO push + redeploy  
- Free Render disk / cold starts can wipe or idle SQLite if disk not attached  
- Docs still mention older service UUID `6b8f3cd7-…` in places — PRIMARY id is `srv-dabgrrp5efls73anlhe0`  
- No email-based password reset (signed-in `change_password` only)  
- Fear & Greed / burns / unlocks / whale feeds absent (UNAVAILABLE / Phase 2+)  

## Missing (this evolution)

| Item | Phase |
|------|-------|
| Support MCCC / Donate (BTC/ETH/SOL + QR) | B |
| About / Privacy / Terms pages | C |
| Hero positioning polish + Support nav/footer | C |
| Postgres migration docs (keep SQLite working) | D |
| Modular chain explorer providers | E |
| Analyst VERIFIED / CALCULATED / INFERENCE labels | E |
| Academy / journey / watchlist honesty polish | F |
| Tests, security notes, redeploy PRIMARY | G |

---

## Production blockers

1. **Git remote lag** — push via ENELO required for GitHub → Render auto-build.  
2. **Persistence** — PRIMARY should keep `/data` disk + `MCCC_DATA_DIR=/data`.  
3. **Optional keys** — markets/AI/explorers degrade gracefully without keys; never crash.  
4. **Secrets** — never commit `RENDER_API_KEY`, `AI_API_KEY`, admin passwords.  

---

## Phased plan (this run)

| Phase | Goal | Status target |
|-------|------|---------------|
| A | Audit → `MCCC_BUILD_STATUS.md`, DEPLOYMENT/SECURITY | Done in-repo |
| B | Donate page + env defaults + tests | Ship early |
| C | Hero, nav, About/Privacy/Terms, friendly errors | Ship |
| D | Auth harden + Postgres path docs (SQLite stays) | Ship docs + light harden |
| E | Explorers modular + Analyst label vocabulary | Ship foundation |
| F | Academy / Start Crypto / projects / watchlists honesty | Light evolve |
| G | Tests green, commit, bundle, redeploy PRIMARY, smoke | Ship |

---

## DEMO vs LIVE (honest)

| Surface | Mode |
|---------|------|
| CoinGecko markets | LIVE when reachable; else DEMO |
| Wallet balances | LIVE via Etherscan/RPC when possible; DEMO addresses labelled |
| Intelligence / RWA seeds | DEMO labelled until sourced adapters |
| Calendar / some intel events | DEMO seeds |
| Donate addresses | Public static (env-configurable) — not “earnings stats” |
| PRO payments | Not enabled — never fake success |
| Chain explorers beyond ETH public paths | UNAVAILABLE until real provider |

