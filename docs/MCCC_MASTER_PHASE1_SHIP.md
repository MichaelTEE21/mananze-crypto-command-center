# MCCC Phase 1 Ship — v2.4.0 Foundation

## Commit

- **SHA:** _(filled after local commit)_
- **Version:** `2.4.0`
- **Branch:** `main` (ahead of origin; parent/ENELO pushes)
- **Bundle:** `/workspace/mccc-phase1-2.4.0.bundle` (for ENELO)

## What shipped (Phase 1 only)

| Item | Detail |
|------|--------|
| Homepage | Hero MCCC / DON'T JUST WATCH…; universal search; ANALYSE CTA; philosophy line |
| Universal search | `src/mccc/universal_search.py` + Search page chips + ANALYSE → Intelligence Report |
| Nav | Sidebar structure + Tokens + Calendar pages; roadmap expander for Whales/Protocols/Ecosystems |
| Token Intelligence | `token_intel.py` + `pages/26_Tokens.py` — market sourced; holders/tokenomics/locks UNAVAILABLE |
| Wallet | ANALYSE CTA on Wallet Tracking → report engine; public-only validation unchanged |
| Calendar | `calendar_events` schema + `calendar_service` + `pages/27_Calendar.py` Month/List + DEMO seeds |
| Plan | `docs/MCCC_MASTER_PLAN.md` Phases 1–8 from real audit |
| Container | `Dockerfile` + `.dockerignore` + healthcheck on `/_stcore/health` |
| Paths | `MCCC_DATA_DIR` / `MCCC_DB_PATH` for volume mounts |

## Tests

- Full `pytest -q` — see count in final report.
- New: `tests/test_phase1_foundation.py` (entity detection, wallet public-only, calendar schema, token placeholders, version).

## Deploy / production status (honest — no invented URL)

### Requirements audit (exact)

| Item | Value |
|------|--------|
| Framework | Streamlit **1.39.0** (long-running server + WebSockets) |
| Entrypoint | `streamlit run app.py --server.port=8501 --server.address=0.0.0.0` |
| Python | 3.12+ (`runtime.txt` → 3.12.8) |
| Deps | `requirements.txt` (streamlit, pandas, plotly, requests, python-dotenv, altair, pytest) |
| DB | SQLite file (`MCCC_DB_PATH` or `MCCC_DATA_DIR/mccc.db`) — **not durable on ephemeral disk** |
| Jobs | No background worker required for Phase 1; intelligence refresh is button-driven |
| Cache | In-process TTL for market_provider |
| Ports | **8501** |
| Secrets | Optional: `COINGECKO_API_KEY`, `ETHERSCAN_API_KEY`, `AI_API_KEY`, `AUTH_SECRET`, admin bootstrap |

### Vercel attempt

- Team available: `mananze` (hobby). Linked projects are Technocore-related, not MCCC.
- Vercel docs/runtime model: **serverless functions / SSR frameworks** — **no Streamlit long-running server support**.
- **DEPLOYMENT STATUS (Vercel): BLOCKED — incompatible platform** (not attempted as fake static/serverless wrap).
- Next.js rewrite for Vercel: **out of Phase 1** (documented in master plan Phase 8+).

### PRIMARY public host: **Render** (after GitHub push)

1. Push `main` via ENELO to `MichaelTEE21/mananze-crypto-command-center`.
2. Render Blueprint (`render.yaml`) **or** Web Service → Docker → root `Dockerfile`.
3. Attach persistent disk at `/data`; env `MCCC_DATA_DIR=/data`, `MCCC_DB_PATH=/data/mccc.db`.
4. Start command (Docker uses `scripts/start.sh`):  
   `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Health check: `/_stcore/health`
6. Optional secrets from `.env.example` in Render dashboard.

**Alternatives:** Streamlit Community Cloud (native); Railway/Fly (same Dockerfile).  
**Streamlit Community Cloud (SECOND):** same repo `app.py` + secrets — mirror/demo URL.

**Vercel:** blocked (serverless ≠ Streamlit long-running server).

### This environment

- No Docker daemon / Railway / Render / Fly CLI authenticated in the box.
- `gh` present; push deferred to parent ENELO per instructions.
- **PRODUCTION URL:** none verified from this run.

## Known limitations

- Calendar DEMO seeds only — burns/unlocks/airdrops not live-fed.  
- Token holders/tokenomics/locks explicitly UNAVAILABLE.  
- SQLite on serverless/ephemeral hosts loses data — use volume or future Postgres.  
- CoinGecko/RPC rate limits → DEMO / UNAVAILABLE labels.  
- Vercel cannot host this app as-is.

## Next step (Phase 2 start)

1. ENELO push + Streamlit Community Cloud (or Docker PaaS) deploy → obtain real HTTPS URL.  
2. Begin Phase 2: sourced unlock/burn adapters → calendar population with provenance.
