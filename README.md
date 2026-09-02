# MANANZE CRYPTO COMMAND CENTER (MCCC)

**Understand Crypto. Read the Chain. Learn as You Go.**

DON'T JUST WATCH CRYPTO. UNDERSTAND IT. · Search. Analyse. Learn. Monitor. Act.

Premium local Streamlit dashboard for crypto intelligence & education.
Built for **B=MananzeZA**. Never stores seed phrases, private keys, or passwords.

**Version:** `2.5.0`

## What works out of the box

| Area | Status |
|------|--------|
| Command Center cockpit | Works — markets LIVE/DEMO, inventory snapshots |
| Markets / Market APIs | Works — CoinGecko when reachable; DEMO fallback labelled |
| Project / Airdrop trackers | Works — kanban, tasks, research timeline, soft FREE limits |
| Wallet tracking | Works — **public addresses only**; beginner gate; secrets rejected |
| Portfolio / Watchlist / Notifications | Works — local SQLite; alerts architecture |
| Education + quizzes / glossary | Works — local markdown catalog |
| AI Assistant | Works — rule-based default; optional LLM if `AI_API_KEY` set |
| Partner Links + Exchange / Wallet directories | Works — `official_url` ≠ `referral_url`; disclosures |
| Account (register/login/profile/password/delete) | Works — scrypt; soft-delete; guest mode OK |
| PRO Architecture | Soft gates + flags — **payments Coming Soon** (never faked) |
| Admin + Diagnostics | Admin password / `is_admin`; Diagnostics when `MCCC_DEV=1` |
| Search / Research / Bookmarks / Resources | Works |
| Intelligence Center | Works — sourced events + **Intelligence Reports**; DEMO labelled |
| Intelligence Report | Works — wallet/token/project/protocol/contract/RWA; Search→Analyse→Understand |
| Universal Search / Command Center front door | Works — entity chips + ANALYSE → Report |
| Token Intelligence | Works — market sourced; holders/tokenomics/locks UNAVAILABLE (Phase 2) |
| Calendar | Works — schema + Month/List + DEMO seeds (live feeds Phase 2–3) |
| RWA Intelligence | Works — profiles, disclosure framework, DEMO seeds |
| Support MCCC / Donate | Works — BTC/ETH/SOL public addresses + QR (env or defaults) |
| About / Privacy / Terms | Works — lightweight Streamlit pages |
| Chain Explorers | Works — ETH/BTC/SOL providers; else UNAVAILABLE |

## What needs keys (optional)

| Env | Needed for |
|-----|------------|
| `COINGECKO_API_KEY` | Higher CoinGecko rate limits (free tier works without) |
| `ETHERSCAN_API_KEY` | Public explorer balances on Wallet Tracking |
| `AI_API_KEY` (+ base/model) | LLM answers; otherwise rule-based only |
| `MCCC_ADMIN_PASSWORD` | Non-DEMO admin unlock (DEMO default: `mccc-admin-demo`) |
| `MCCC_BOOTSTRAP_ADMIN_EMAIL` | Auto-promote that Account email to `is_admin` |
| `MCCC_PRO_UNLOCK=1` | Local PRO UI unlock (**not** a payment) |
| `MCCC_DEV=1` | Diagnostics page + Admin Diagnostics tab |
| `AUTH_SECRET` | Stable session salt (ephemeral if unset) |
| `MCCC_BTC/ETH/SOL_DONATION_ADDRESS` | Public donation addresses (defaults documented) |

Missing optional keys **warn at startup** — the app never crashes for them.

## Demo vs live

- **DEMO / EXAMPLE**: labelled portfolio samples, synthetic history, seed rows, `0xDEMO…` balances.
- **Live (when reachable)**: CoinGecko markets + `/global` via `market_provider` (TTL cache). Source + LIVE/DEMO badges in UI.
- Assistant never invents live prices. Fear & Greed shown as **unavailable** unless a reliable free API is wired.

## PRO / payments (honest)

- Planned price: **$4/mo**.
- Checkout UI is **disabled**. Copy states: **"PRO payments are not yet enabled."**
- Local unlocks: feature flags, `set_tier("pro")` architecture toggle, or `MCCC_PRO_UNLOCK=1`.
- **Never** presents a fake successful Stripe/charge state.

### Free soft limits (guest or free tier)

| Resource | Default max |
|----------|-------------|
| Projects | 10 (`MCCC_FREE_MAX_PROJECTS`) |
| Wallets | 5 (`MCCC_FREE_MAX_WALLETS`) |
| Airdrops | 15 (`MCCC_FREE_MAX_AIRDROPS`) |

Clear upgrade CTA → PRO page when hit. PRO / unlock = unlimited.

## Security

- Never accept/store seed phrases, private keys, wallet/exchange passwords, or 2FA secrets.
- App Account password ≠ chain keys (scrypt hashed locally).
- Partner/exchange links keep separate `official_url` vs `referral_url` (never hardcode referrals).
- First admin: set `MCCC_BOOTSTRAP_ADMIN_EMAIL` (or Admin → bootstrap_admin_email setting) to your registered email.

## Requirements

- Python 3.12+ (3.13 OK)
- Windows PowerShell preferred; POSIX also supported

## Setup (Windows / PowerShell)

```powershell
cd \path\to\mccc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # optional — edit keys
.\START.ps1
```

Or double-click `START.bat`. Both scripts create `.venv` if missing, `pip install`, copy `.env.example` → `.env` when needed, and run Streamlit. `load_dotenv` runs from `app.py` / `ui.page_setup`.

## Setup (POSIX)

```bash
cd /path/to/mccc
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional
streamlit run app.py --server.port 8501
```

App URL: http://localhost:8501

## Tests

```bash
source .venv/bin/activate && pytest -q
```

## Layout

```
mccc/
  app.py                 # Command Center
  pages/                 # Multipage surfaces (incl. Account, PRO, Admin, Diagnostics)
  src/mccc/              # auth, subscriptions, config, security, market_provider, ui, db, …
  content/education/     # markdown lessons
  data/                  # SQLite (gitignored)
  docs/                  # AUDIT, PLAN, DELIVERABLE, MCCC20_SHIP
  tests/
  START.ps1 / START.bat
  requirements.txt
  .env.example
```

## Partner Links

Central SQLite `partner_links` + `partner_link_clicks` (no IP / UA / PII).

- **Public:** Partner Directory / Start Here — Active only. Affiliate disclosure + seed-phrase warning.
- **Admin:** password via `MCCC_ADMIN_PASSWORD` **or** signed-in `is_admin` user.
- Never hardcode referral URLs in pages — edit via Admin only.

## Limitations / roadmap

- CoinGecko / RPC may rate-limit → DEMO fallback (labelled).
- PRO Stripe checkout is Coming Soon — no payments processed.
- Assistant defaults to rule-based unless `AI_API_KEY` is set.
- Fear & Greed unavailable until a reliable free feed is wired.
- Hosted multi-tenant hardening is out of scope for local 2.0.0.


## Deployment (production)

See **`docs/DEPLOYMENT.md`** (PRIMARY Render `srv-dabgrrp5efls73anlhe0`). Also `docs/SECURITY.md`, `docs/MCCC_BUILD_STATUS.md`.

## Deployment (production) — legacy

MCCC is a **long-running Streamlit** app (not a Vercel serverless function). Full audit: `docs/MCCC_DEPLOYMENT_AUDIT.md`. Host guide: `docs/DEPLOY.md`. Vercel blocker: `docs/MCCC_VERCEL_BLOCKER.md`.

### Quick paths

| Path | Status |
|------|--------|
| **Render (preferred)** | `render.yaml` Blueprint or MCP `create_web_service` (Python) — volume/disk at `/data` |
| **Docker** | `Dockerfile` + `docker-compose.yml` — `docker compose up --build` |
| **Streamlit Community Cloud** | One-click: connect GitHub → Main file `app.py` → Deploy |
| **Vercel** | **Not supported** for Streamlit without a full rewrite (see docs) |

```bash
# Local prod-sim
cp .env.example .env
docker compose up --build
# Health: curl http://localhost:8501/_stcore/health
```

**Persistence:** SQLite at `data/mccc.db`. On hosts, mount a durable volume at `/data` (`MCCC_DATA_DIR`). `DATABASE_URL` is ignored until a Postgres adapter exists.

**DEMO vs LIVE:** CoinGecko LIVE when reachable; otherwise labelled DEMO. Never invent live prices.

## Changelog

See `CHANGELOG.md` for 2.0.0 release notes.

GitHub push when requested — do not push until asked.
