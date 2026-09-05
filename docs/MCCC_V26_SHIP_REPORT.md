# MCCC 2.6.0 Partner Ecosystem — Ship Report

**For:** B=MananzeZA · **Date:** 2026-09-05 (Africa/Johannesburg, SAST)
**Baseline:** v2.5.0 `8e8e996` on `origin/main`
**Release commit:** `5020eb7` (`5020eb76ea24419aceb5af0a7efb7f4d28a6b5c5`) — if this disagrees with `git rev-parse HEAD`, trust git (self-hash embed lag).
**Deploy note:** Parent pushes to GitHub + redeploys **existing PRIMARY** Render service only — **no new Render services**. Do not push from this box.

---

## Outcome

Local **v2.6.0 Partner Ecosystem** work audited, critical gap filled (`partner_cta` uses `require_active=True`), **207 tests passed**, one clean local commit on `main`. Version `__version__ == "2.6.0"`.

## Commit

- **SHA:** `5020eb76ea24419aceb5af0a7efb7f4d28a6b5c5`
- **Short:** `5020eb7`
- **Message:** `release: MCCC 2.6.0 Partner Ecosystem (directory, hubs, referral routing, analytics)`
- **Pushed:** NO (by design)

## Files touched (summary)

**Core**
- `src/mccc/__init__.py` — version `2.6.0`
- `src/mccc/partners.py` — categories, `resolve_outbound` / `get_outbound_url`, disclosures, analytics + date dimension, ecosystem summary, demo seed, category migrate
- `src/mccc/db.py` — `source_page` on clicks; category migrate on init
- `src/mccc/ui.py` — nav links (Crypto Directory, hubs, Partner Analytics); `partner_cta` + `referral_leave_disclosure`; Active-only outbound routing

**Pages (new)**
- `pages/33_Crypto_Directory.py`
- `pages/34_DEX_Hub.py`
- `pages/35_Admin_Partner_Analytics.py`

**Pages (updated)**
- `pages/11_Partner_Directory.py`, `12_Admin_Partner_Links.py`, `17_Start_Here.py`
- `pages/19_Wallet_Directory.py` (Wallet Hub), `20_Exchange_Directory.py` (Exchange Hub)
- `pages/4_Wallet_Tracking.py` (minor)
- `app.py` — Command Center partner ecosystem strip + hub links

**Tests / docs**
- `tests/test_partner_ecosystem_v26.py` (new), `tests/test_partners.py` (+ version asserts)
- `CHANGELOG.md`, `README.md`, `docs/MCCC_PARTNER_ECOSYSTEM_SHIP.md`, this report

## Feature checklist (implemented)

| Item | Status |
|------|--------|
| Crypto Directory (categories + listings) | Done — page 33 |
| Partner Links admin + central partner service | Done — page 12 + partners.py |
| Referral routing (partner URL if active else official) | Done — resolve_outbound / partner_cta |
| Referral disclosure copy | Done — REFERRAL_LEAVE_DISCLOSURE + UI helpers |
| Privacy-conscious click analytics + admin dashboard | Done — aggregates only; page 35 |
| Wallet Hub / CEX Hub / DEX Hub | Done — pages 19 / 20 / 34 |
| Command Center partner ecosystem summary | Done — app.py |
| Nav links; Streamlit-valid emoji (no invalid hexagon) | Done — validated via Streamlit validate_emoji |

## Tests

```
207 passed
```

(`pytest tests/` — local `.venv`, 2026-09-05 SAST)

## Remaining gaps (non-blocking)

- DEMO partner rows still use `example.com` until real partners are added in Admin
- Click analytics are aggregate-only (no funnel / attribution)
- Postgres migration noted in code (`POSTGRES_NOTE`), not implemented — SQLite default
- Exchange Hub still also reads the separate `exchanges` table; partner CTAs remain the referral source of truth
- No automated E2E Streamlit UI smoke in CI

## How to smoke-test

1. `cd /workspace/mccc && .venv/bin/streamlit run app.py`
2. Command Center → **Partner ecosystem** strip shows category counts + hub links
3. Open **Crypto Directory** → filter categories; DEMO badges visible; CTAs show official vs referral caption
4. **Wallet Hub / Exchange Hub / DEX Hub** → never-ask-keys banners; no seed/password fields
5. Admin password (`MCCC_ADMIN_PASSWORD` or DEMO `mccc-admin-demo`) → **Partner Links** CRUD + **Partner Analytics** (platform / category / date)
6. Click **Track & open** on a listing → analytics total increments (no IP/UA stored)
7. Disable a partner in Admin → CTA must fall back to **official** URL only

## Blockers for ENELO push / Render redeploy

- **None for code.** Parent must: push this commit to GitHub `main`, then redeploy the **existing** Render service (do not create a new service).
- Ensure Render env still has any existing secrets; do not commit `.env`.
- Free-plan / Docker+/data constraints from prior deploy docs still apply — unchanged by this feature set.
