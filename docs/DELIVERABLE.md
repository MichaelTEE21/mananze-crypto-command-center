# MCCC Deliverable draft — v1.2 UI upgrade

**Date:** 2026-09-02 (Africa/Johannesburg)  
**Scope:** Premium Streamlit command-center UI wired to existing foundation services.  
**Constraint:** Keep Partner Links; keep Streamlit; never accept seeds/keys; never present DEMO as live.

## Summary

Upgraded MCCC from stage-shell pages to a denser crypto command center:

- Design system polish in `src/mccc/ui.py` (cards, badges, empty/error helpers, sidebar version / PRO / unread).
- Command Center cockpit uses `market_provider.get_overview` + real `portfolio` when rows exist.
- New pages: Markets, Portfolio, Watchlist, Notifications, Account, Start Here, Search.
- Upgraded trackers (kanban projects, richer airdrops + tasks), Wallet beginner gate, AI → `ai_service`, Education progress, PRO Coming Soon Stripe ($4/mo, no fake payment).
- Education content expanded (basics + security).
- Thin services: `education.py`, `airdrop_tasks.py`, `subscriptions.py`.

## Acceptance checklist

- [x] App imports cleanly (pages + package)
- [x] `pytest -q` green
- [x] Functional forms save to SQLite
- [x] No hardcoded referral URLs in pages
- [x] No fake live prices / DEMO always labelled
- [x] Partner Links pages kept (11/12)
- [x] Seeds/keys refused (auth, wallets, AI, warnings)

## Out of scope / later

- Real Stripe checkout
- Background alert workers
- Hosted multi-tenant auth hardening
- Fear & Greed (marked unavailable)

## How to verify

```bash
cd /workspace/mccc
source .venv/bin/activate
pytest -q
streamlit run app.py --server.port 8501
```

Smoke: Start Here → Account register → Portfolio add asset → Markets LIVE/DEMO badge → Airdrop task toggle → Education mark complete → Admin unlock.
