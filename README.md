# MANANZE CRYPTO COMMAND CENTER (MCCC)

**The operating system for a crypto researcher.**

Premium local Streamlit dashboard for crypto intelligence & education.
Built for **B=MananzeZA**. Never stores seed phrases, private keys, or passwords.

**Version:** `1.2.0-dev`

## Stages / pages

| # | Page | What it does |
|--:|------|--------------|
| — | Command Center (`app.py`) | Cockpit: market overview, portfolio summary, snapshots, quick links |
| 0/17 | Start Here | Beginner onboarding + partner wallet/CEX links |
| 1 | Markets | Rich BTC/ETH/SOL + markets via `market_provider` |
| 2 | Project Tracker | Kanban by stage + extended fields |
| 3 | Airdrop Tracker | Statuses, filters, tasks checklist |
| 4 | Wallet Tracking | Public addresses only + beginner security gate |
| 5 | Market APIs | Slim CoinGecko tinkering (cache control) |
| 6 | Analytics | Plotly charts (live/DEMO labelled) |
| 7 | AI Assistant | `ai_service` rule-based + optional LLM |
| 8 | Education | Markdown lessons + progress |
| 9 | User Analytics | Aggregate local usage & inventory |
| 10 | PRO Architecture | Coming Soon Stripe · $4/mo planned · never fake payment |
| 11 | Partner Directory | Central DB links (keep) |
| 12 | Admin Partner Links | CRUD + clicks · password **or** `is_admin` |
| 13 | Portfolio | CRUD + PnL + CSV |
| 14 | Watchlist | Items + alerts + local evaluator |
| 15 | Notifications | Local inbox |
| 16 | Account | Register / login / profile / onboarding |
| 18 | Search | Global search projects/airdrops/wallets/education |

## Demo vs live

- **DEMO / EXAMPLE**: labelled portfolio samples, synthetic history, seed rows, `0xDEMO…` balances.
- **Live (when reachable)**: CoinGecko markets + `/global` overview via `market_provider` (TTL cache). Source + LIVE/DEMO badges in UI.
- Assistant never invents live prices. Fear & Greed shown as **unavailable** unless a reliable free API is wired.

## Requirements

- Python 3.12+ (3.13 OK)
- Windows PowerShell preferred; POSIX also supported

## Setup (PowerShell)

```powershell
cd \path\to\mccc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # optional
.\START.ps1
```

Or double-click `START.bat`.

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
  pages/                 # Multipage surfaces
  src/mccc/              # auth, portfolio, watchlist, notifications, market_provider,
                         # ai_service, partners, education, subscriptions, airdrop_tasks, ui, db
  content/education/     # markdown lessons (basics + security)
  data/                  # SQLite (gitignored)
  docs/                  # AUDIT, MASTER_PLAN, DELIVERABLE
  tests/
  START.ps1 / START.bat
  requirements.txt
  .env.example
```

## Env vars (see `.env.example`)

| Var | Purpose |
|-----|---------|
| `COINGECKO_API_KEY` | Optional CoinGecko key |
| `ETHERSCAN_API_KEY` | Optional explorer balances |
| `MCCC_PRO_UNLOCK` | `1` unlocks PRO flags locally (not payment) |
| `MCCC_ADMIN_PASSWORD` | Admin Partner Links gate (DEMO default if unset) |
| `AI_API_KEY` / `AI_API_BASE` / `AI_MODEL` | Optional LLM for assistant |
| `AUTH_SECRET` | Optional session salt |

## Partner Links

Central SQLite `partner_links` + `partner_link_clicks` (no IP / UA / PII).

- **Public:** Partner Directory / Start Here — Active only. Affiliate disclosure + seed-phrase warning.
- **Admin:** password via `MCCC_ADMIN_PASSWORD` **or** signed-in `is_admin` user.
- Never hardcode referral URLs in pages — edit via Admin only.

Disclosure: *Some links on MCCC may be partner or referral links. MCCC may receive compensation if you sign up through eligible links, at no additional cost to you.*

## Security

- No private keys / seeds / passwords accepted in research forms.
- Optional API keys only via `.env` (never commit secrets).
- Usage analytics local-only.
- Soft-gate auth: app works without login; Account enables multi-profile.

## Limitations

- CoinGecko / RPC may rate-limit → DEMO fallback (labelled).
- PRO Stripe checkout is Coming Soon — no payments processed.
- Assistant defaults to rule-based unless `AI_API_KEY` is set.

## Next step

GitHub push when you say so. Do not push until requested.
