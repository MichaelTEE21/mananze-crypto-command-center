# MCCC Production Deployment Guide

**Dual-deploy (same GitHub repo only — do not fork):**

1. **Render first (PRIMARY)** — Docker Web Service / Blueprint  
2. **Streamlit Community Cloud second** — native Streamlit from same `main`

See also: `MCCC_DEPLOYMENT_AUDIT.md`, `MCCC_VERCEL_BLOCKER.md`, `MCCC_MASTER_PHASE1_SHIP.md`.

## Start command (Render / Docker)

```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

Repo entrypoint: `scripts/start.sh` (used by `Dockerfile` `CMD`).

Health check path: `/_stcore/health`

Persistence: mount disk at **`/data`**; set `MCCC_DATA_DIR=/data` and `MCCC_DB_PATH=/data/mccc.db`.

## 1) Render (PRIMARY)

### MCP `create_web_service` (Python — no Docker in MCP)

After Render OAuth works (`list_workspaces` not `unauthorized`) and GitHub has latest `main`:

- **repo:** `https://github.com/MichaelTEE21/mananze-crypto-command-center.git`
- **branch:** `main`
- **runtime:** `python`
- **buildCommand:** `pip install -r requirements.txt`
- **startCommand:** `bash scripts/start.sh`
- **plan:** `free` or `starter`
- **envVars:** `MCCC_DATA_DIR=./data`, `AUTH_SECRET`, optional keys from `.env.example`

### Dashboard Blueprint / Docker (secondary path for disk)


1. Push `main` via ENELO to `MichaelTEE21/mananze-crypto-command-center` (same repo — no fork).
2. Render → **Blueprint** (`render.yaml`) **or** **Web Service** → Docker → root `Dockerfile`.
3. Attach **persistent disk** mountPath `/data` (1GB+).
4. Env (non-secret): `MCCC_DATA_DIR=/data`, `MCCC_DB_PATH=/data/mccc.db`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.
5. Optional secrets from `.env.example` in Render dashboard.
6. Deploy → copy public HTTPS URL after health passes.

## 2) Streamlit Community Cloud (SECOND — same repo)

1. https://share.streamlit.io → sign in with GitHub.
2. **New app** → repo `MichaelTEE21/mananze-crypto-command-center` → branch `main`.
3. Main file: `app.py` · Python ≥ 3.12.
4. Secrets (TOML) from `.env.example` names.
5. Deploy → second public URL (demo / mirror). Note: Community Cloud disk may reset on rebuild — prefer Render disk for durable SQLite.

## Vercel

**Blocked** for Streamlit — see `MCCC_VERCEL_BLOCKER.md`. No fake URL.

## DEMO vs LIVE

| Label | Meaning |
|-------|---------|
| LIVE | Provider reachable; UI LIVE chip |
| DEMO / DATA UNAVAILABLE | Labelled fallback — never silent invent |

## Local prod-sim

```bash
docker compose up --build
# http://localhost:8501
```

## Existing Render service (do not duplicate)

- **PRIMARY Service ID:** `srv-dabgrrp5efls73anlhe0`
- **URL:** https://mananze-crypto-command-center.onrender.com
- **Dashboard:** https://dashboard.render.com/web/srv-dabgrrp5efls73anlhe0
- (Legacy connector token UUID `6b8f3cd7-…` may appear in older notes — use PRIMARY id above)
- Connect repo `MichaelTEE21/mananze-crypto-command-center` branch `main`
- Env: `MCCC_DATA_DIR=/data`, `MCCC_DB_PATH=/data/mccc.db`
- Start: Docker `CMD` → `scripts/start.sh` (binds `$PORT`)
- Health: `/_stcore/health`
- Secrets only in Render dashboard (never git)
