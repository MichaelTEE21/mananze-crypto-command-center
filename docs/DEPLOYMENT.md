# MCCC Deployment

**PRIMARY (do not duplicate):** Render Web Service  
- **Service ID:** `srv-dabgrrp5efls73anlhe0`  
- **URL:** https://mananze-crypto-command-center.onrender.com  
- **Repo:** `MichaelTEE21/mananze-crypto-command-center` · branch `main`  
- **Health:** `/_stcore/health`  
- **Start:** `bash scripts/start.sh` (Docker `CMD`)  

Secondary mirror (optional): Streamlit Community Cloud from same `main`.  
**Vercel:** blocked for Streamlit — see `MCCC_VERCEL_BLOCKER.md`.  
**Technocore:** separate product — never deploy into MCCC.

## Env (non-secret examples)

```
MCCC_DATA_DIR=/data
MCCC_DB_PATH=/data/mccc.db
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
MCCC_PRO_UNLOCK=0
MCCC_DEV=0
# Public donation addresses (defaults in code if unset)
MCCC_BTC_DONATION_ADDRESS=bc1q7a9uh6utn85gjhs5dakn3kkazsmt9s4q37cn32
MCCC_ETH_DONATION_ADDRESS=0x6d04cff44c379cb89050ddb9b55e3b29d3ffc091
MCCC_SOL_DONATION_ADDRESS=BgQgsr63rbRNsjLabU5toVwj1itkfLDHMLxCCo29tCwB
```

Secrets (`AUTH_SECRET`, `AI_API_KEY`, `ETHERSCAN_API_KEY`, `MCCC_ADMIN_PASSWORD`, …) only in Render dashboard — never git.

## Database

- **Today:** SQLite on disk (`MCCC_DB_PATH`). Keep working on free Render.  
- **Later:** `DATABASE_URL` Postgres (e.g. Neon) — see `SECURITY.md` / build status. Adapter is reserved; do not force mid-flight if it breaks free deploy.

## Redeploy PRIMARY

```bash
# Use Render REST API with RENDER_API_KEY from connector secrets (never print key)
curl -s -X POST "https://api.render.com/v1/services/srv-dabgrrp5efls73anlhe0/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":"do_not_clear"}'
```

Smoke after deploy:

```bash
curl -fsS https://mananze-crypto-command-center.onrender.com/_stcore/health
curl -fsS -o /dev/null -w "%{http_code}\n" https://mananze-crypto-command-center.onrender.com/
```

## Local prod-sim

```bash
docker compose up --build
# http://localhost:8501
```

Also see legacy notes in `docs/DEPLOY.md` and `docs/MCCC_DEPLOYMENT_AUDIT.md`.
