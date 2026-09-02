# MCCC Production Deployment Guide

**Preferred host:** **Render**  
**Status:** Artifacts ready (Dockerfile, `render.yaml`, compose). Public URL requires Render MCP OAuth (or Dashboard) + GitHub push of current tree.

See also: `MCCC_DEPLOYMENT_AUDIT.md`, `MCCC_VERCEL_BLOCKER.md`.

## DEMO vs LIVE (data providers)

| Label | Meaning |
|-------|---------|
| **LIVE** | CoinGecko (and optional Etherscan / LLM) reachable; UI shows LIVE chip |
| **DEMO / EXAMPLE** | Labelled fallback or seed samples — never presented as live market truth |

## 1) Render — preferred production host

### A) Cursor Render MCP (once OAuth connected)

1. Cursor → MCP / Plugins → **Render** → **Authenticate** (browser OAuth). Verify with `list_workspaces` (must not return `unauthorized`).
2. Ensure GitHub has the latest `main` (Phase 1 + deploy files). Push via ENELO/`gh` if local is ahead.
3. `create_web_service`:
   - **name:** `mccc`
   - **runtime:** `python` (MCP does not create full Docker/disk services — use Blueprint for disk)
   - **repo:** `https://github.com/MichaelTEE21/mananze-crypto-command-center.git`
   - **branch:** `main`
   - **buildCommand:** `pip install -r requirements.txt`
   - **startCommand:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - **plan:** `free` or `starter`
   - **envVars:** `MCCC_DATA_DIR=./data`, `AUTH_SECRET=<random>`, optional API keys
4. Wait for deploy live → curl `https://<service>.onrender.com/` and `/_stcore/health`.

### B) Dashboard Blueprint (Docker + disk)

1. https://dashboard.render.com → New → Blueprint
2. Connect GitHub repo `mananze-crypto-command-center`
3. Apply `render.yaml` (Docker runtime, health `/_stcore/health`, disk mount **`/data`**, `MCCC_DATA_DIR=/data`)
4. Set secrets in Dashboard (never commit them)

**Persistence:** Disk at `/data` on paid/starter Blueprint. Free MCP Python service → SQLite may be ephemeral across deploys.

**Neon:** Available in Cursor; app still **ignores** `DATABASE_URL` (SQLite only). Do not provision Postgres until an adapter exists.

## 2) Streamlit Community Cloud (fallback one-click)

https://share.streamlit.io → GitHub → Main file `app.py` → Deploy. Secrets via TOML.

## 3) Local Docker prod-sim

```bash
cp .env.example .env
docker compose up --build
curl -fsS http://localhost:8501/_stcore/health
```

## 4) Vercel — blocked

See `MCCC_VERCEL_BLOCKER.md`. No fake URL.

## Smoke checklist (real public URL only)

1. Homepage HTTP 200  
2. `/_stcore/health` OK  
3. Command Center loads; LIVE or labelled DEMO  
4. No secrets in git  
5. (If disk) data survives refresh  

## Connector status (this environment)

| Connector | Status |
|-----------|--------|
| Render MCP | Plugin installed; calls may return `unauthorized` until user re-clicks Authenticate |
| Neon MCP | Ready — unused (no Postgres adapter) |
| Vercel MCP | Ready — Streamlit incompatible |
| `gh` auth | Not logged in — prefer ENELO push |
| Docker daemon | Not on box |
