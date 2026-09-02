# MCCC Intelligence Report — Ship notes (v2.3.0)

## How to run locally

```bash
cd /workspace/mccc   # or your checkout
source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py --server.port 8501
# Sidebar → Intelligence Center → Analyse · Intelligence Report
# Or Search → ANALYSE → / Wallet Tracking → Intelligence Report
pytest -q
```

Windows: `.\START.ps1` or `START.bat`.

## Deployment status (honest)

| Target | Status |
|--------|--------|
| Local Streamlit | **Supported** — primary path |
| Streamlit Community Cloud | Compatible in principle (needs repo + secrets as env); not configured in this commit |
| Vercel | **Blocker:** MCCC is a Streamlit (Python long-running) app. It cannot deploy to Vercel “as-is” without a separate hosting architecture (e.g. container / Streamlit Cloud / VM). No fake Vercel deploy. |
| Durable multi-tenant DB on ephemeral hosts | SQLite local path is **not** durable on Vercel-like FS — same honesty as Intelligence/RWA Phase 1 |

Production URL: **none from this phase** (local/green tests + commit only).

## Security

- Public addresses only; seeds/private keys/passwords/recovery rejected.
- No secrets in repo; `.env.example` has empty placeholders.
- AI refuses credential-like report context.

## Known limitations

- Transaction history feed not fully wired — reports show DATA UNAVAILABLE rather than inventing txs.
- TVL never invented; protocol reports mark TVL unavailable until a verified provider is added.
- CoinGecko / RPC / Etherscan may rate-limit → DEMO or DATA UNAVAILABLE.
- “What changed?” depends on prior local observations in SQLite.
- Identity: never claims wallet belongs to a named party without authoritative source.

## Recommended next step

1. Parent/ENELO push to `MichaelTEE21/mananze-crypto-command-center` when asked.
2. Optional: Streamlit Community Cloud deploy with env keys.
3. Optional: verified explorer tx list + TVL provider adapters behind same `ReportDataProvider` interface.

## Commit

- SHA: `680be2ac53ecbec455ce2621c05ae2f1b349bf80` (`680be2a`)
- Tests: **159 passed**
- Branch: `main` ahead of origin — **not pushed** (parent / ENELO)
