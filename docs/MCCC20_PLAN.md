# MCCC 2.0 Plan (Phases 1–14)

**Product:** MANANZE CRYPTO COMMAND CENTER inside `/workspace/mccc` (no separate project).  
**Baseline:** v1.2.0-dev features stay. Phase 1 bumps version to **2.0.0-dev**.  
**Constraints:** No seed/key storage. Honest DEMO/LIVE. `official_url` ≠ hardcoded referral. Never wipe SQLite data.

Legend: **Exists (v1.2)** = already on disk — wire/improve, don’t rebuild. **New** = 2.0 work.

---

## Phase 1 — Architecture cleanup *(implement now)*

| Item | Status |
|------|--------|
| Version → `2.0.0-dev` | New |
| `src/mccc/services/` facades (market/ai re-exports; legacy imports work) | New |
| Schema: exchanges, resources, announcements, bookmarks, research_events, project_tags, app_settings; `research_notes.project_id` | New tables / column |
| `security.py` + wire wallets/auth/forms | New + harden Exists |
| `load_dotenv` at app startup | Improve (ui already had it) |
| CHANGELOG + security tests green | New |
| KEEP Partner Links, portfolio, watchlist, auth, market_provider, START.* | Exists |

**Exit:** `pytest` all green; no GitHub push; stop here for this task.

---

## Phase 2 — Exchanges directory

**Exists:** Partner Links CEX/DEX categories; official vs referral fields.  
**New:** Admin CRUD UI for `exchanges` table; optional one-way sync helper from Active CEX/DEX partners (copy official/referral — never invent referrals). Public browse page with difficulty/region/security_info. Status Active|Disabled.

---

## Phase 3 — Resources + bookmarks

**Exists:** Ad-hoc URLs on projects/airdrops.  
**New:** `resources` CRUD (optional `project_id`, `is_official`, click_count). `bookmarks` UI (item_type/ref, tags, priority, favourite). Search page indexes bookmarks.

---

## Phase 4 — Research timeline & tags

**Exists:** `research_notes`, project tracker extended columns.  
**New:** Wire `project_id` on notes; `research_events` timeline on Project Tracker; `project_tags` multi-tag filter. No data wipe — migrate only.

---

## Phase 5 — Announcements + app settings

**Exists:** Feature flags, sidebar badges.  
**New:** Published announcements strip (respect `expires_at`). Settings page/section over `app_settings` (theme prefs already on profiles — don’t duplicate blindly).

---

## Phase 6 — Market / portfolio / watchlist honesty polish

**Exists:** `market_provider` TTL, portfolio PnL, watchlist+alerts, LIVE/DEMO badges.  
**Improve:** Consistent sidebar LIVE/DEMO chip; never invent prices; CSV import validation; empty states with labelled DEMO samples only behind expanders.

---

## Phase 7 — Project & Airdrop tracker upgrades

**Exists:** CRUD + stages/statuses + airdrop_tasks service/UI start.  
**Improve:** Forms expose remaining extended fields; kanban polish; task checklist completeness; link resources/events from Phase 3–4.

---

## Phase 8 — Auth UX + account hardening

**Exists:** scrypt auth, Account page, session helpers, security rejection.  
**Improve:** Clearer copy that app password ≠ chain keys; route all password-like fields through `reject_sensitive_credential`; optional local multi-profile; keep env admin break-glass for Partner admin.

---

## Phase 9 — Notifications + alert evaluator

**Exists:** notifications inbox, alerts table, unread sidebar count.  
**New:** Local evaluator (button/session tick): watchlist thresholds vs `market_provider` → notifications; label DEMO vs live sources.

---

## Phase 10 — Education expansion

**Exists:** `content/education/*.md`, progress service, Education page.  
**Improve:** Longer modules; quiz stubs; mark-complete UX; link key_safety / seed_phrase lessons from wallet beginner gate.

---

## Phase 11 — AI assistant deepening

**Exists:** rule + optional LLM, refusal, research notes, usage log.  
**Improve:** Mode badge; cite local notes/projects; never invent live quotes; all prompts through security; optional deep-research behind PRO flag only.

---

## Phase 12 — Partner / Admin polish

**Exists:** Full Partner Directory + Admin CRUD + disclosures.  
**Improve:** `source_page` everywhere; richer click charts; exchange sync entry-points; reinforce official vs referral in UI copy. **Do not replace** partner data model.

---

## Phase 13 — PRO / subscriptions (no payments)

**Exists:** feature_flags, subscriptions stub (`coming_soon`), PRO page mock.  
**Improve:** Read-model tying tier → flags; still **no Stripe/checkout**; honest “not charged” copy.

---

## Phase 14 — UI polish, test freeze, docs, release prep

**Exists:** Dark terminal CSS, hero/cards/badges.  
**Improve:** Denser terminal metrics; hub `st.page_link` consistency; full pytest + security suite; README/CHANGELOG for 2.0.0 release candidate. Still no mandatory GitHub push until requested.

---

## Explicit non-goals (all phases)

- Separate repo / Next.js rewrite  
- Custodial wallets, signing, seed storage  
- Hardcoded referral URLs  
- Real payment processing  
- Deleting Partner Links / portfolio / watchlist / auth / market_provider  

---

## What v1.2 already gave us (don’t rebuild)

| Capability | Where |
|------------|-------|
| Market provider + cache | `market_provider.py` |
| Portfolio + CSV | `portfolio.py`, page 13 |
| Watchlist + alerts schema | `watchlist.py`, page 14 |
| Notifications | `notifications.py`, page 15 |
| Auth + Account | `auth.py`, page 16 |
| AI service | `ai_service.py`, page 7 |
| Partners official/referral | `partners.py`, pages 11–12 |
| Airdrop tasks / education / subscriptions | thin modules + pages |
| dotenv in UI bootstrap | `ui.py` |

Phase 1 only adds facades, schema, and central security on top of this base.
