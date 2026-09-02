# MCCC Intelligence Report — Plan (from real audit)

**Product:** MANANZE CRYPTO COMMAND CENTER (MCCC)  
**User:** B=MananzeZA  
**Base:** `b271fe0` / v2.2.0 (RWA Phase 1 + Intelligence Agent Phase 1)  
**Target version:** 2.3.0  
**Rule:** Build on existing code. Do not rebuild. Technocore out of scope.

## Phase 1 — What exists (audit findings)

| Area | Location | Status |
|------|----------|--------|
| Framework | Streamlit 1.39 multipage (`app.py` + `pages/`) | Working |
| Package | `src/mccc/` version `2.2.0` | Working |
| DB | SQLite `data/mccc.db` via `db.init_db` + migrations | Working |
| Markets | `market_provider.CoinGeckoProvider` LIVE/DEMO labelled | Working |
| Wallets | `wallets.validate_public_address` + Etherscan/RPC soft-fail; public only | Working |
| Security | `security.reject_sensitive_credential` (mnemonic/hex key/markers) | Working |
| Search | `search.search_all` — projects/airdrops/wallets/exchanges/education/resources/notes/rwa/intelligence | Working |
| Intelligence Center | `pages/24_Intelligence_Center.py` + `intelligence/` pipeline | Working — event feed, not entity reports |
| RWA | `pages/25_RWA_Intelligence.py` + `intelligence/rwa/` | Working |
| AI Assistant | `ai_service` rule + optional LLM; refuses secrets; market via provider | Working — not report-context-aware yet |
| Education | `content/education/*.md` + `education.py` | Working |
| Analytics | pages 6 / 9 | Working |
| Deploy | Local Streamlit only; START.ps1/bat; **no Vercel config** | Honest blocker for Vercel-as-is |
| Tests | 132 passed at audit start | Green |

### Gaps this phase closes

1. No unified **Intelligence Report** for Project | Token | Wallet | Protocol | Contract | RWA entity.
2. Intelligence Center is feed-centric; missing Search → Analyse → Understand product brain.
3. Wallet / Search UX copy not yet matching user-provided “ANALYZE A PUBLIC WALLET” / “SEARCH THE BLOCKCHAIN” language.
4. No historical observation store for “What changed?” between analyses.
5. AI Assistant not grounded on the current report session context.
6. Metric explainers (TVL etc.) and Beginner vs Advanced report modes incomplete.

### Non-negotiables (carry forward)

- Public addresses only — never seeds / private keys / passwords / recovery.
- Never invent txs, wallets, market data, TVL, partnerships, live stats.
- DEMO/SYNTHETIC always labelled; provider failure → DATA UNAVAILABLE or labelled demo.
- Risk language: Investigate further / Potential risk indicator / Insufficient data / No conclusion.
- Identity: “this address interacted with…” — never “belongs to X” without verified authoritative source.
- No financial advice / buy-sell instructions.

## Architecture (Phases 4–5)

```
Providers → Normalisation → Analytics → Intelligence → Report → Education
```

Reuse existing providers (`wallets`, `market_provider`, `IntelligenceRepository`, `RWAService`). New code lives under `src/mccc/intelligence/report/` — replaceable providers, no parallel duplicate systems.

Engine helpers (codebase naming):

- `analyze_wallet` / `analyze_token` / `analyze_protocol` / `analyze_project` / `analyze_contract` / `analyze_rwa`
- `detect_activity_change`
- `concentration` indicators
- `summarize_transactions` (only when reliable data present)
- Risk indicators (neutral research language)
- Beginner summary + metric explainers

## Report sections (all required)

1. Executive summary  
2. What is this? (plain + Advanced View)  
3. On-chain activity (provenance on every metric)  
4. Wallet/address intelligence (public only)  
5. Token intelligence (verified vs estimated vs user-provided)  
6. Risk / red flag (neutral)  
7. What changed? (vs prior observations; invent no causes)  
8. Beginner explanation  
9. Sources (real only)  
10. Confidence / data quality: HIGH | MEDIUM | LOW  

## UI / Education / RWA (Phases 6–8)

- Intelligence Center gains Analyse tab: Search → Analyse → Understand → Investigate.
- Search page + Wallet Tracking adopt user-provided UX copy + public-only security block.
- Preserve RWA vertical; connect via `entity_type=rwa` into same report engine.
- Beginner Mode vs Advanced Mode toggle on report view.

## AI (Phase 9)

- Prefer context-aware of `st.session_state` current report summary.
- Never invent missing chain data; refuse secrets; label DEMO.

## Privacy / Tests / Deploy (Phases 10–12)

- Public data only; security scan in tests.
- Tests: valid/invalid inputs; provider success/timeout/error/missing/partial/rate-limit; UI-state helpers; secrets rejection.
- Deploy: Streamlit Cloud / local documented. **Streamlit cannot deploy to Vercel as-is** — document honest blocker; ship green tests + local commit. Do not push unless remote verified (parent/ENELO).

## Delivery checklist

- [x] Audit → this plan  
- [x] Report engine + repository  
- [x] Intelligence Center integration  
- [x] Search + Wallet UX copy  
- [x] AI report context  
- [x] Tests green  
- [x] CHANGELOG / README / version 2.3.0  
- [x] Local commit (no push)  
