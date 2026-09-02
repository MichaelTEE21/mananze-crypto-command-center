# Why MCCC cannot run on Vercel without compromise (2026-09-02)

## Verdict

**Streamlit MCCC cannot be deployed as a production Streamlit app on Vercel today without rewriting the product.**

Vercel MCP is authenticated for team `mananze` (Hobby). That does **not** make Streamlit compatible.

## Precise technical blockers

1. **Long-running process vs serverless**  
   MCCC starts with `streamlit run app.py`, which boots a persistent Tornado HTTP server. Vercel’s primary compute model is short-lived serverless / edge functions with request timeouts — not a always-on Streamlit process.

2. **WebSockets / bidirectional session protocol**  
   Streamlit’s UI requires a persistent WebSocket (or equivalent) session between browser and server for widget state, reruns, and multipage navigation. Classic Vercel Functions are request/response oriented; even where experimental WebSocket helpers exist for custom ASGI apps, they are not a drop-in for the Streamlit runtime.

3. **Writable local filesystem (SQLite)**  
   MCCC persists to `data/mccc.db` on local disk. Serverless filesystems are ephemeral/read-only for durable app state. A Vercel deploy would lose research trackers, accounts, and partner links unless the app were re-architected onto external storage (Postgres/Neon, etc.).

4. **In-process TTL cache & multipage Python package**  
   Market cache and `src/mccc/*` assume a long-lived Python process with local package imports — not a static export or single Lambda handler.

## What we will NOT do

- Add a fake `vercel.json` that claims Streamlit succeeds.
- Invent a `*.vercel.app` production URL.
- Rewrite MCCC to Next.js solely for this mission.

## Honest Next.js migration path (document only — not executed)

If public hosting on Vercel is a hard requirement later:

1. Extract domain logic (`db`, market providers, intelligence) into a shared Python API **or** reimplement data layer in TypeScript against Postgres (Neon).
2. Rebuild UI in Next.js App Router; keep DEMO vs LIVE labelling rules.
3. Replace SQLite with `DATABASE_URL` (Neon) and session auth suitable for multi-tenant hosting.
4. Deploy API + web on Vercel; never claim feature parity until trackers/auth/markets are re-proven with tests.

Until then, prefer **Streamlit Community Cloud** or a **Docker long-running host** (Railway / Render / Fly).
