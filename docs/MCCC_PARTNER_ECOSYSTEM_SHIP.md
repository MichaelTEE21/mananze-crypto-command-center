# MCCC 2.6.0 — Partner Ecosystem Ship

**For:** B=MananzeZA · **From:** executor · **Date:** 2026-09-02 (Africa/Johannesburg)  
**Baseline:** v2.5.0 `8e8e996` (Support / explorers / donate / UI foundation — production stable)  
**Deploy:** Parent pushes + redeploys **existing PRIMARY** Render service — **no new services**.

---

## Reused
- `src/mccc/partners.py` CRUD + `partner_links` / `partner_link_clicks` schema
- Admin Partner Links (`12_`), Partner Directory (`11_`), Wallet/Exchange directories
- `ui.partner_cta`, affiliate + seed disclosures, `design_system.py`
- Command Center market/research cockpit wiring

## Added / extended
- Categories → Wallets, CEX, DEX, Explorers, Tools, Education (+ legacy normalize/migrate)
- `resolve_outbound` / `get_outbound_url` / `partner_ecosystem_summary` / date analytics
- Pages: `33_Crypto_Directory`, `34_DEX_Hub`, `35_Admin_Partner_Analytics`
- Hub branding + never-ask-keys on Wallet / Exchange / DEX
- Command Center partner ecosystem section
- `REFERRAL_LEAVE_DISCLOSURE`; Postgres note (SQLite remains default)
- Tests: `test_partners.py` expanded + `test_partner_ecosystem_v26.py`

## Out of scope
- Technocore · new Render services · secrets in git · Academy/AI/Research deep rewrites

## Limitations
- DEMO partner rows use `example.com` until real partners are added in Admin
- Click analytics are aggregate only (no funnel attribution)
- Postgres migration documented, not implemented
- Exchange Hub still also uses the separate `exchanges` table (kept); partner CTAs are the referral source of truth

## ENELO
- Bundle: `/workspace/mccc-2.6.0-partner.bundle` (for parent push)
- Do **not** create new Render services — redeploy PRIMARY only
