# MANANZE CRYPTO COMMAND CENTER (MCCC)

**The operating system for a crypto researcher.**

Premium local Streamlit dashboard for crypto intelligence & education.
Built for **B=MananzeZA**. Never stores seed phrases, private keys, or passwords.

## Stages

| Stage | Page | What it does |
|------:|------|--------------|
| 1 | Command Center (`app.py`) | Dark shell, nav hub, DEMO portfolio, market snapshot |
| 2 | Project Tracker | List/add/edit research projects — SQLite |
| 3 | Airdrop Tracker | Airdrops + eligibility notes — DEMO seed + editable |
| 4 | Wallet Tracking | Public watch addresses; DEMO or public RPC balances |
| 5 | Market APIs | CoinGecko live prices; DEMO fallback if offline |
| 6 | Analytics | Plotly charts on DEMO / fetched data |
| 7 | AI Assistant | Rule-based checklists + note structuring (no LLM) |
| 8 | Education | Static markdown lessons |
| 9 | User Analytics | Local page/case usage stats in SQLite |
| 10 | PRO Architecture | Feature flags + paywall mock (not charged) |

## Demo vs live

- **DEMO / EXAMPLE**: portfolio, synthetic price history, seed projects/airdrops, `0xDEMO…` balances — always labelled.
- **Live (when reachable)**: CoinGecko `coins/markets`; optional Cloudflare ETH RPC / Etherscan for public balances. Source labelled in UI.
- Assistant never invents live prices.

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

If Python is missing, scripts print: **Please tell MANANZE.**

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

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

```bash
source .venv/bin/activate && pytest
```

## Layout

```
mccc/
  app.py                 # Stage 1
  pages/                 # Stages 2–10
  src/mccc/              # db, market, wallets, assistant, ui, demo_data
  content/education/     # markdown lessons
  data/                  # SQLite (gitignored)
  tests/
  START.ps1 / START.bat
  requirements.txt
  .env.example
```

## Security

- No private keys / seeds / passwords accepted.
- Optional API keys only via `.env` (never commit secrets).
- Usage analytics are local-only; no PII required.

## Limitations

- CoinGecko / RPC may rate-limit → DEMO fallback.
- Wallet balances are ETH-oriented; multi-token needs explorer keys.
- PRO is architecture mock — no payments.
- Assistant is rule-based, not an LLM.

## Next step

GitHub push when you say so. Do not push until requested.
