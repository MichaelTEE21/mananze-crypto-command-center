# MCCC Deployment Audit (evidence-based)

**Audit date:** 2026-09-02 (Africa/Johannesburg)  
**Repo:** `MichaelTEE21/mananze-crypto-command-center`  
**Tree:** `/workspace/mccc`  
**App version:** `2.3.0` (`src/mccc/__init__.py`)  
**Branch at audit:** `main` (local ahead of `origin/main`; Phase 1 calendar schema may be uncommitted in `src/mccc/db.py` — deploy work is additive only)

## Framework & runtime

| Item | Finding | Evidence |
|------|---------|----------|
| Framework | **Streamlit** multipage app | `requirements.txt` → `streamlit==1.39.0`; `app.py` imports `streamlit as st`; `pages/*.py` |
| Python | **3.12+** (3.13 OK). Box used 3.13.5 for tests | `README.md` Requirements; local `.venv` |
| Entry point | **`app.py`** via `streamlit run app.py` | `START.ps1` / `START.bat`; README POSIX section |
| Port (local) | **8501** | `.streamlit/config.toml` `[server] port = 8501` |
| Headless | `headless = true` | `.streamlit/config.toml` |
| Theme | Dark custom theme | `.streamlit/config.toml` |

## Dependencies (`requirements.txt`)

Pinned:

- `streamlit==1.39.0`
- `plotly==5.24.1`
- `pandas==2.2.3`
- `requests==2.32.3`
- `python-dotenv==1.0.1`
- `altair==5.4.1`
- `pytest==8.3.3` (dev/test; safe to leave in prod image for smoke)

No `psycopg2`, no Redis, no Celery, no FastAPI/Flask.

## Env vars (from `.env.example`)

All optional for boot (`src/mccc/config.py` validates with warnings only):

| Variable | Role |
|----------|------|
| `COINGECKO_API_KEY` | Optional CoinGecko rate limits |
| `ETHERSCAN_API_KEY` | Optional public explorer balances |
| `MCCC_PRO_UNLOCK` | Local PRO UI unlock (not payment) |
| `MCCC_ADMIN_PASSWORD` | Admin gate (DEMO default if unset) |
| `MCCC_BOOTSTRAP_ADMIN_EMAIL` | Promote matching Account email to `is_admin` |
| `MCCC_DEV` | Diagnostics |
| `MCCC_FREE_MAX_*` | Soft FREE limits |
| `AI_API_KEY` / `AI_API_BASE` / `AI_MODEL` | Optional LLM assistant |
| `AUTH_SECRET` | Session salt |
| `DATABASE_URL` | **Documented but ignored** — MCCC uses local SQLite only |

Secrets must never be committed (`.gitignore` covers `.env`, `*.db`, `.streamlit/secrets.toml`).

## External APIs

| Provider | Mode | Notes |
|----------|------|-------|
| CoinGecko `api.coingecko.com` | **LIVE when reachable** | `src/mccc/market_provider.py`, `market.py`; DEMO fallback labelled |
| Etherscan (optional) | LIVE if key | Wallet Tracking |
| OpenAI-compatible (optional) | LIVE if `AI_API_KEY` | Else rule-based assistant |
| Fear & Greed | **Unavailable** | Explicitly not wired |

UI badges: LIVE vs DEMO / EXAMPLE — never invent prices.

## Database & persistence

| Item | Finding |
|------|---------|
| Engine | **SQLite** via `sqlite3` |
| Path | `data/mccc.db` (`src/mccc/paths.py` → `DB_PATH`) |
| Init | `init_db()` on page load |
| `DATABASE_URL` | Ignored today (`config.validate_config` warns if set) |
| Ephemeral risk on hosts | **High** if container filesystem is non-persistent — mount a volume at `/app/data` or migrate later |
| Postgres / Neon | **Not supported in code yet.** Neon MCP is available in Cursor, but wiring would require a new adapter. Do not break local SQLite. Document only. |

## Cache / jobs / websockets / filesystem

| Concern | Finding |
|---------|---------|
| Cache | In-process **TTL cache (~60s)** for CoinGecko in `market_provider._TTLCache` — not Redis |
| Background jobs | **None** (no Celery/APScheduler workers) |
| WebSockets | Streamlit’s own WebSocket/session protocol (Tornado) — **required** for the UI to work |
| Writable FS | SQLite writes under `data/`; education content read-only under `content/` |
| Multiprocess | Single Streamlit server process expected |

## Build / start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Docker (this mission):

```bash
docker build -t mccc .
docker run --rm -p 8501:8501 -v mccc-data:/app/data --env-file .env mccc
```

Health endpoint (Streamlit): `GET /_stcore/health`

## Host fit summary

| Host | Fit | Why |
|------|-----|-----|
| **Vercel** | **NO** (current Streamlit app) | Serverless / short-lived functions; no long-running Streamlit + WebSocket session server without rewriting the product. See `docs/MCCC_VERCEL_BLOCKER.md`. MCP authenticated (`mananze` team) but cannot honestly deploy this app as-is. |
| **Render** | **PREFERRED production**  | Python web service via MCP or Blueprint; same repo. Streamlit Cloud is secondary same-repo deploy. |
| **Railway / Render / Fly.io** | **Good with Docker** | Long-running containers + volume for SQLite. No Railway/Render/Fly CLI or API tokens in this environment. |
| **Neon Postgres** | **Future only** | MCP ready; app ignores `DATABASE_URL` today. |

## Out of scope

- Technocore
- Rewriting MCCC to Next.js solely for Vercel (document migration path only)
- Fake production URLs or fake live market data

## Coordination note

Phase 1 product work (e.g. `calendar_events` in `src/mccc/db.py`) may land on the same tree. Deploy mission prefers **additive** files (`Dockerfile`, docs, compose) and does not discard product edits.
