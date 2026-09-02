# MCCC Deploy Ship Notes

**Date:** 2026-09-02 (Africa/Johannesburg)

## Delivered artifacts

- `Dockerfile` — python:3.12-slim, `MCCC_DATA_DIR=/data`, binds `$PORT`
- `.dockerignore`
- `docker-compose.yml` — volume `mccc-data` → `/data`
- `render.yaml` — Render Blueprint (Docker + `/data` disk)
- `railway.toml` — secondary
- `runtime.txt` / `packages.txt` — Streamlit Cloud helpers
- Docs: `MCCC_DEPLOYMENT_AUDIT.md`, `MCCC_VERCEL_BLOCKER.md`, `DEPLOY.md`

## Tests / smoke (local)

- pytest: all green after version pin `2.4.0`
- Streamlit smoke: homepage HTTP 200, `/_stcore/health` → `ok` on `127.0.0.1:8599`

## Production URL

**Not live yet.** Render MCP returned `unauthorized` despite plugin present. No invented URL.

## Exact next user actions

1. **Cursor → Render MCP → Authenticate** (OAuth) until `list_workspaces` succeeds.
2. **Push** this tree to GitHub (`MichaelTEE21/mananze-crypto-command-center` `main`) via ENELO/`gh`.
3. Re-run deploy: MCP `create_web_service` (Python) **or** Dashboard Blueprint from `render.yaml`.
4. Curl the real `*.onrender.com` URL and record it here.
