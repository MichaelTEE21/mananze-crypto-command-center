# MCCC Deploy Ship Notes (2026-09-02 SAST)

## Git
- **HEAD:** `136e2923a990c3e2e1308c4a58f4093580cb2ff7`
- **Commit:** MCCC 2.4.0 Phase 1 + production deploy artifacts (Render-first)
- **Bundle:** `/workspace/mccc-phase1-2.4.0.bundle` (origin/main..HEAD)
- **Push:** blocked — `gh`/`git push` not authenticated (ENELO must push)

## Artifacts
Dockerfile (`$PORT`, `MCCC_DATA_DIR=/data`), `.dockerignore`, `docker-compose.yml`,
`render.yaml` (Docker Blueprint secondary), `railway.toml`, `scripts/start.sh`,
`runtime.txt`, `packages.txt`, deploy docs + Vercel blocker.

## Local verification
- pytest: **174 passed** (2.4.0)
- Streamlit smoke: homepage HTTP 200 + `/_stcore/health` → ok (local :8599)

## Production URLs
**None yet — do not invent.**

### Blockers
1. **Render MCP** returns `unauthorized` — user must Cursor → MCP → Render → **Authenticate**
2. **GitHub** lacks commit `b144704` — ENELO push `mccc-deploy.bundle` / `git push`
3. After push + auth: MCP `create_web_service` runtime=python, start `bash scripts/start.sh`
4. Then Streamlit Community Cloud from **same** repo (no fork) → smoke that URL too

READY only after each public URL is curl-smoked.
