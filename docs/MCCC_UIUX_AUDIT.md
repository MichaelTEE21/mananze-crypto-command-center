# MCCC UI/UX Audit (Streamlit — redesign, not polish)

**Date:** 2026-09-02 · **Constraint:** Stay on Streamlit; push CSS + components so it does **not** feel default Streamlit. No Next.js rewrite.

## Layers (keep separate)

| Layer | Owns | Must not mix |
|-------|------|--------------|
| **UI** | `ui.py`, `design_system.py`, page shells, CSS tokens, nav | Business rules, API keys |
| **Logic** | `auth`, `market_provider`, `intelligence/*`, `wallets`, `donations` | Presentation HTML |
| **Data** | SQLite / providers / DEMO seeds | Invented chain facts |

Backends to **RETAIN** unchanged in behavior: Intelligence Report, RWA, auth/PRO, markets LIVE/DEMO, Support/donate addresses, explorers.

---

## What looks Streamlit-generic (REMOVE / hide)

| Issue | Action |
|-------|--------|
| Default multipage chrome / Deploy button / menu | Hide via CSS (`#MainMenu`, `header`, `footer`, decoration) |
| Rainbow progress bar | Restyle or neutralize |
| Dense emoji-heavy sidebar | Sparse icons; professional labels |
| Raw `st.metric` / unstyled forms | Prefer design-system cards + mono metrics |
| Generic white borders / default widgets | Tokenized dark fintech surfaces |
| Long undifferentiated page stacks | Experience groups: Dashboard / Explore / … |
| Aggressive donate modal every visit | **REMOVED** — always accessible, never annoying |

## REDESIGN

1. **Design tokens** — color, type, spacing, radius, elevation in `design_system.py`.
2. **Page shell** — hierarchy: What happened → Why it matters → Investigate → Learn next.
3. **Nav experiences** — Dashboard, Explore, Wallets, On-chain, Analytics, AI Analyst, Academy, Projects, Watchlist, Support MCCC (+ legal collapse).
4. **Components** — cards, badges, alerts, empty/loading/error, tables, chart frames, CTA row.
5. **Support** — persistent nav + dashboard CTA + dedicated page; first-visit delayed soft prompt only.
6. **Responsive** — desktop density; tablet/mobile stacked rows, readable type.

## RETAIN

- Dark theme baseline (IBM Plex / JetBrains Mono direction)
- LIVE/DEMO chips and honesty labels (VERIFIED / CALCULATED / INFERENCE / UNAVAILABLE)
- Universal search → ANALYSE funnel
- Seed-phrase warnings; public-only wallets
- Existing page backends and routes (rename labels, don’t delete features)

## Experience map (target nav)

| Nav label | Primary route(s) |
|-----------|------------------|
| Dashboard | `app.py` |
| Explore | Search + Intelligence + Tokens |
| Wallets | Wallet Tracking + Directory |
| On-chain | Chain Explorers |
| Analytics | Analytics + Markets |
| AI Analyst | AI Assistant |
| Academy | Education + Start Crypto |
| Projects | Project + Airdrop trackers |
| Watchlist | Watchlist + Notifications |
| Support MCCC | Donate page |

## Success criteria

- Feels like a **crypto intelligence terminal / premium SaaS**, not a demo Streamlit app.
- Data-dense but scannable; beginner explainers under key metrics.
- Support always one click away; never nagging.
- Tests green; PRIMARY Render only redeployed after commit/bundle.
