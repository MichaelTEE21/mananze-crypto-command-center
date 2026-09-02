# MCCC 2.0.0 — Ship summary (Phases 12–14)

**For:** B=MananzeZA · **From:** executor (Phases 12–14) · **Date:** 2026-09-02 (Africa/Johannesburg)  
**Version:** `2.0.0` · **Tests:** **98 passed** · **No git push** (parent owns push)

---

## 1. What changed

### Phase 12 — Authentication polish
- Account page: register / login / logout, profile edit, onboarding goals + experience, **password change (scrypt)**, **soft-delete account** (cascades user-scoped rows; shared projects/airdrops/wallets kept)
- Session helpers documented in `auth.py` (`get_session_user` / `login` / `logout` / guest mode)
- Guest mode still OK with FREE soft limits
- Admin bootstrap: `MCCC_BOOTSTRAP_ADMIN_EMAIL` **or** `app_settings.bootstrap_admin_email` (Admin → Featured)

### Phase 13 — PRO feature gating
- FREE limits: **10 projects / 5 wallets / 15 airdrops** (env-overridable)
- Soft gate + upgrade CTA on Project / Airdrop / Wallet add forms
- PRO page: **$4/mo**, disabled checkout, **"PRO payments are not yet enabled."** — never fake success
- Gated: advanced analytics **CSV export**, watchlist alerts, AI deep-research (`has_pro_feature` + flags + `MCCC_PRO_UNLOCK`)

### Phase 14 — Production hardening
- Version bumped to **2.0.0**
- README rewritten (what works / keys / Windows START / security / DEMO / tests / roadmap)
- `pages/23_Diagnostics.py` when `MCCC_DEV=1`; Admin Diagnostics tab when `MCCC_DEV=1`
- `config.validate_config()` warn-only at startup (no crash, no secret echo)
- `ui.footer` version on all pages; CHANGELOG + DELIVERABLE finalized
- START.ps1 / START.bat unchanged & working; `load_dotenv` via app/ui

**Security held:** no seeds/keys/passwords for external services; DEMO/LIVE honest; Partner Links kept; no fake Stripe.

---

## 2. Created

| Path | Role |
|------|------|
| `src/mccc/config.py` | Optional env validation + public diagnostics snapshot |
| `pages/23_Diagnostics.py` | Dev diagnostics (`MCCC_DEV=1`) |
| `tests/test_phase12_14.py` | Auth / limits / bootstrap / config / security regressions |
| `docs/MCCC20_SHIP.md` | This ship note |
| `docs/DELIVERABLE.md` | Rewritten 2.0 final report |

---

## 3. Modified (high-signal)

| Path | Role |
|------|------|
| `src/mccc/__init__.py` | `__version__ = "2.0.0"` |
| `src/mccc/auth.py` | change_password, update_profile, delete_account, bootstrap, soft-delete |
| `src/mccc/subscriptions.py` | FREE limits, check_limit, has_pro_feature, CTA copy |
| `src/mccc/db.py` | `users.deleted_at` migration |
| `src/mccc/ui.py` | validate/bootstrap in page_setup; `upgrade_cta` |
| `pages/16_Account.py` | Full auth polish UI |
| `pages/10_PRO_Architecture.py` | Honest Coming Soon + limits |
| `pages/2_*` / `3_*` / `4_*` | Soft FREE gates |
| `pages/6_Analytics.py` | PRO export gate |
| `pages/7_AI_Assistant.py` / `14_Watchlist.py` | PRO feature gates |
| `pages/22_Admin.py` | Bootstrap email + Diagnostics tab |
| All pages + `app.py` | Footer / light startup validate |
| `README.md` / `CHANGELOG.md` / `.env.example` | Release docs |

---

## 4. Tests

- Suite: `pytest -q` under `/workspace/mccc`
- New: `tests/test_phase12_14.py` (15 cases)
- Also updated `test_ui_helpers` version assert → `2.0.0`

## 5. Pass / fail

**PASS — 98 tests green.**

## 6. Remaining known limitations

- Stripe / real PRO payments not implemented (Coming Soon, honest)
- CoinGecko / explorers may fall back to labelled DEMO
- LLM assist needs `AI_API_KEY`; else rule-based
- Fear & Greed unavailable
- `DATABASE_URL` ignored (local SQLite)
- Soft FREE limits count whole local DB (shared guest inventory + DEMO seeds)

## 7. Env vars

| Var | Purpose |
|-----|---------|
| `COINGECKO_API_KEY` | Optional CG Pro |
| `ETHERSCAN_API_KEY` | Optional explorer balances |
| `AI_API_KEY` / `AI_API_BASE` / `AI_MODEL` | Optional LLM |
| `MCCC_PRO_UNLOCK` | `1` = local PRO unlock (not payment) |
| `MCCC_ADMIN_PASSWORD` | Admin gate (DEMO default if unset) |
| `MCCC_BOOTSTRAP_ADMIN_EMAIL` | Promote matching user → `is_admin` |
| `MCCC_DEV` | `1` = Diagnostics page + Admin tab |
| `MCCC_FREE_MAX_PROJECTS` / `_WALLETS` / `_AIRDROPS` | Soft limit overrides |
| `AUTH_SECRET` | Session salt |
| `DATABASE_URL` | Ignored |

---

**Parent next step:** review → push when user asks (executor did not push).
