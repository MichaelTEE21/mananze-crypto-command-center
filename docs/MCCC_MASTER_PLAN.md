# MCCC Master Plan (v2.4+) — real audit + Phases 1–8

**Repo:** `https://github.com/MichaelTEE21/mananze-crypto-command-center`  
**Framework:** Streamlit 1.39 + Python 3.12, SQLite local (`data/mccc.db`), package under `src/mccc/`  
**Out of scope forever here:** Technocore (separate product).  
**Rules:** public addresses only; never invent live txs/burns/unlocks/TVL/tokenomics; label DEMO / DATA UNAVAILABLE; FACT/VERIFIED/ANALYSIS/ESTIMATE/UNVERIFIED/UNKNOWN; no financial advice.

---

## Audit snapshot (Phase 1 run — HEAD before 2.4.0 ≈ `680be2a` / `bb98bad`)

| Area | Status before Phase 1 | Notes |
|------|----------------------|-------|
| Command Center (`app.py`) | Exists — market cockpit | Transformed into search front door in 2.4.0 |
| Search (`18_Search.py` + `search.py`) | Category search | Extended with universal entity detection / chips |
| Intelligence Center + Report | **Shipped 2.3.0** | Reuse for ANALYSE routing |
| RWA Intelligence | **Shipped 2.2.0** | Keep |
| Projects / Airdrops / Wallets | Working trackers | Keep; wallet ANALYSE CTA elevated |
| Markets / Analytics / AI / Education | Working | Keep |
| Auth / PRO / Portfolio / Watchlist / Notifications | Working | Soft PRO; payments not enabled |
| Partner / Exchange / Wallet directories | Working | Keep |
| Calendar | **Missing** | Added foundation 2.4.0 |
| Token Intelligence page | Markets only | Added `26_Tokens.py` + `token_intel.py` |
| Universal search entity chips | Partial via report validators | Added `universal_search.py` |
| Burns / unlocks live pipelines | Absent | Phase 2–3 |
| Whales / Protocols / Ecosystems deep intel | Absent / interim dirs | Phase 4 |
| Alerts polish / Agent MONITOR→ / X publish | Absent | Phase 5–7 |
| Deploy | Local Streamlit only | See ship notes — **not Vercel-as-is** |

**Tests before Phase 1:** 159 passed (Intelligence Report ship).

---

## Phase 1 — Foundation (THIS RUN) ✅ target

1. Audit + this plan file from real findings.  
2. Homepage / Command Center: hero, universal search, **ANALYSE** CTA, philosophy line.  
3. Universal Search: detect 0x / $TICKER / names; chips; route to Intelligence Report.  
4. Navigation structure (sidebar) toward Command Center, Search, Intelligence, Airdrops, Tokens, Wallets, Calendar, Projects, Analytics, RWA, Learn, Agent, Alerts, My Research; Phase N hooks labelled.  
5. Token Intelligence foundation (market via `market_provider`; holders/tokenomics/locks = UNAVAILABLE).  
6. Wallet Intelligence UX — public only + ANALYSE into report engine.  
7. Calendar architecture — `calendar_events` schema, Month/List, type filters, DEMO seeds, intel click-through hooks.  
8. Version **2.4.0**, tests green, local commit, ENELO push bundle — **no fake Phases 2–8**.

---

## Phase 2 — Burns + unlocks pipelines (document only)

- Sourced burn/unlock adapters behind provider interface.  
- Populate calendar event types `burn` / `unlock` with provenance.  
- Never invent schedules; UNAVAILABLE when source fails.  
- Whale-watch scaffolding (public large movers only when sourced).

## Phase 3 — Airdrop Command Center statuses

- Status model polish (DISCOVERED→…→CLAIMED) + calendar airdrop population.  
- Eligibility notes hygiene; no fake claim values.

## Phase 4 — Project / protocol / ecosystem deep intel

- Protocol pages beyond Exchange Directory interim.  
- Ecosystem maps; still no invented TVL.

## Phase 5 — Live feed + alerts polish

- Intelligence feed freshness UX; alert evaluator polish; notification routing.

## Phase 6 — Agent MONITOR → research loop

- Agent modes MONITOR / RESEARCH / SUMMARISE (still ≠ silent trading).  
- Grounded on reports + sourced events.

## Phase 7 — X approve/publish (optional)

- Human-in-the-loop draft → approve → publish. Never auto-tweet secrets or advice.

## Phase 8 — Education polish + production hardening

- Lesson paths; production DB (Postgres via `DATABASE_URL`) if multi-tenant; observability.

---

## Deploy reality (honest)

| Target | Fit |
|--------|-----|
| **Vercel** | **Blocker** — Streamlit is a long-running WebSocket server; Vercel is serverless/edge. No supported Streamlit runtime. Do not fake. |
| **Render (PRIMARY)** | Docker Web Service + `render.yaml` + disk `/data`; start via `scripts/start.sh` (`$PORT`). |
| **Streamlit Community Cloud** | Native alternative after GitHub push. |
| **Railway / Fly.io** | Same `Dockerfile` compatible. |
| **Rewrite to Next.js for Vercel** | Out of Phase 1 — migration path only in Phase 8+ if product requires Vercel specifically. |

---

## Security invariants (all phases)

- Never request/store seeds, private keys, recovery phrases, wallet/X passwords.  
- Public addresses only.  
- Secrets stay in env / Streamlit secrets / host secret store — never in git.
