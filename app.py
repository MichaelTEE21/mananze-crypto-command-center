"""
MANANZE CRYPTO COMMAND CENTER (MCCC)
Entry point — premium Command Center cockpit.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass

import pandas as pd
import streamlit as st

from mccc import APP_NAME, APP_TAGLINE, __version__
from mccc.announcements import list_published as list_announcements
from mccc.db import init_db, list_airdrops, list_projects, list_wallets, usage_summary
from mccc.demo_data import DEMO_PORTFOLIO, portfolio_summary as demo_portfolio_summary
from mccc.notifications import list_notifications, unread_count
from mccc.partners import SEED_PHRASE_WARNING, list_partner_links
from mccc.portfolio import compute_summary, list_assets
from mccc.services.market import get_default_provider
from mccc.universal_search import (
    analyse_session_payload,
    detect_search_entity,
    homepage_search_placeholder,
)
from mccc.ui import (
    affiliate_disclosure_short,
    data_mode_chip,
    demo_callout,
    empty_state,
    footer,
    hero,
    metric_card,
    page_setup,
    quick_actions,
    section_header,
    session_user_id,
    status_badge,
)
from mccc.watchlist import list_items as list_watchlist

# Light config validation at startup (never crash)
try:
    from mccc.config import validate_config
    from mccc.auth import maybe_bootstrap_admin

    maybe_bootstrap_admin()
    _cfg_warns = validate_config()
except Exception:
    _cfg_warns = []

# Active / in-flight stages (exclude terminal) — product vocabulary (Phase 4–5)
_ACTIVE_PROJECT_STAGES = {
    "DISCOVERED",
    "RESEARCHING",
    "FARMING",
    "WATCHLIST",
    "WAITING FOR TGE",
}
_UPCOMING_STAGES = {"WAITING FOR TGE", "FARMING"}
_ACTIVE_AIRDROP_STATUSES = {
    "DISCOVERED",
    "RESEARCHING",
    "ACTIVE",
    "WAITING",
}
_DONE_AIRDROP = {"CLAIMED", "COMPLETED", "MISSED", "ARCHIVED"}


def _px(coin: dict | None) -> str:
    if not coin or coin.get("current_price") is None:
        return "—"
    try:
        return f"${float(coin['current_price']):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _chg(coin: dict | None) -> tuple[str, str]:
    """Return (formatted change, delta_kind up|down|flat)."""
    if not coin or coin.get("price_change_percentage_24h") is None:
        return "—", "flat"
    try:
        v = float(coin["price_change_percentage_24h"])
        kind = "up" if v > 0 else "down" if v < 0 else "flat"
        return f"{v:+.2f}%", kind
    except (TypeError, ValueError):
        return "—", "flat"


def _fmt_mcap(mcap) -> str:
    if not mcap:
        return "—"
    try:
        v = float(mcap)
        if v >= 1e12:
            return f"${v / 1e12:.2f}T"
        if v >= 1e9:
            return f"${v / 1e9:.2f}B"
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "—"


page_setup("command_center", "Command Center")

hero(
    "MCCC",
    "DON'T JUST WATCH CRYPTO. UNDERSTAND IT. · v" + __version__,
)
st.markdown(
    '<p style="color:#9aa7b5;letter-spacing:0.12em;font-size:0.85rem;margin:0.2rem 0 0.85rem;">'
    "Search. Analyse. Learn. Monitor. Act."
    "</p>",
    unsafe_allow_html=True,
)

init_db()
uid = session_user_id()
provider = get_default_provider()

# --- Universal Search / ANALYSE front door ---
section_header("Command Center", "Universal search → Intelligence Report")
_q_default = st.session_state.get("mccc_home_q", st.session_state.get("mccc_search_q", ""))
home_q = st.text_input(
    "Universal search",
    value=_q_default,
    placeholder=homepage_search_placeholder(),
    key="mccc_home_search_input",
    label_visibility="collapsed",
).strip()
st.session_state["mccc_home_q"] = home_q
c_a, c_b, c_c = st.columns((2, 1, 1))
with c_a:
    analyse_clicked = st.button("ANALYSE", type="primary", use_container_width=True, key="home_analyse")
with c_b:
    search_clicked = st.button("Search", use_container_width=True, key="home_search")
with c_c:
    st.page_link("pages/24_Intelligence_Center.py", label="Intelligence Center", icon="🛰️")

if analyse_clicked:
    if not home_q:
        st.warning("Enter a wallet, token, contract, project, protocol, or airdrop to analyse.")
    else:
        detected = detect_search_entity(home_q)
        if detected.rejected_secret:
            st.error(detected.error)
        elif not detected.ok:
            st.error(detected.error or "Could not understand that query.")
        else:
            for k, v in analyse_session_payload(detected).items():
                st.session_state[k] = v
            st.switch_page("pages/24_Intelligence_Center.py")
elif search_clicked:
    if not home_q:
        st.info("Type something to search the local research store.")
    else:
        st.session_state["mccc_search_q"] = home_q
        st.switch_page("pages/18_Search.py")

if home_q:
    _det = detect_search_entity(home_q)
    if _det.ok:
        st.caption(
            f"Detected · **{_det.chip}** (`{_det.entity_type}`) · normalised `{_det.normalized}`"
        )
    elif _det.rejected_secret:
        st.error(_det.error)

st.caption(
    f"{APP_NAME} · {APP_TAGLINE} · public data & labelled DEMO only · not financial advice"
)

# --- Market snapshot ---
section_header("Market snapshot", "BTC / ETH / SOL · mcap & dominance when available")
overview, ov_source, ov_live = provider.get_overview()
data_mode_chip(ov_live)
st.caption(f"Source: {ov_source}")
if not ov_live:
    demo_callout("Market overview is DEMO / incomplete — not live market quotes.")

btc_chg, btc_kind = _chg(overview.get("btc"))
eth_chg, eth_kind = _chg(overview.get("eth"))
sol_chg, sol_kind = _chg(overview.get("sol"))

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    metric_card(_px(overview.get("btc")), "BTC", delta=btc_chg, delta_kind=btc_kind)
with m2:
    metric_card(_px(overview.get("eth")), "ETH", delta=eth_chg, delta_kind=eth_kind)
with m3:
    metric_card(_px(overview.get("sol")), "SOL", delta=sol_chg, delta_kind=sol_kind)
with m4:
    metric_card(_fmt_mcap(overview.get("total_market_cap_usd")), "Total mcap")
with m5:
    dom = overview.get("btc_dominance")
    eth_dom = overview.get("eth_dominance")
    dom_s = f"{dom:.1f}%" if isinstance(dom, (int, float)) else "—"
    eth_s = f"{eth_dom:.1f}%" if isinstance(eth_dom, (int, float)) else "—"
    metric_card(dom_s, f"BTC dom · ETH {eth_s}")

st.caption("Fear & Greed: unavailable (no reliable free API wired).")

# --- Load research data ---
projects = list_projects()
airdrops = list_airdrops()
wallets = list_wallets()
watch = list_watchlist(user_id=uid)
assets = list_assets(user_id=uid)
usage = usage_summary()
partner_count = len(list_partner_links(status="Active"))
unread = unread_count(user_id=uid)
notifs = list_notifications(user_id=uid, unread_only=True)[:5]
announcements = list_announcements(limit=5)

active_projects = [
    p for p in projects if (p.get("stage") or "") in _ACTIVE_PROJECT_STAGES
]
upcoming = [p for p in projects if (p.get("stage") or "") in _UPCOMING_STAGES]
active_airdrops = [
    a for a in airdrops if (a.get("status") or "Discovered") in _ACTIVE_AIRDROP_STATUSES
] or [a for a in airdrops if (a.get("status") or "") not in _DONE_AIRDROP]
with_deadline = [a for a in active_airdrops if (a.get("deadline") or "").strip()]

# --- Research cockpit metrics ---
section_header("Research cockpit", "Active trackers at a glance")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    metric_card(str(len(active_projects)), f"Active projects · {len(projects)} total")
with c2:
    metric_card(str(len(upcoming)), "Upcoming stages (Farming / TGE)")
with c3:
    metric_card(str(len(active_airdrops)), f"Active airdrops · {len(with_deadline)} deadlines")
with c4:
    metric_card(str(len(wallets)), f"Watch wallets · {len(watch)} watchlist")
with c5:
    metric_card(str(unread), "Unread notifications")

# Upcoming stages detail
if upcoming:
    with st.expander(f"Upcoming project stages ({len(upcoming)})", expanded=False):
        for p in upcoming[:8]:
            stage = p.get("stage") or "—"
            st.markdown(
                f"**{p.get('name', '—')}** · `{stage}` · {p.get('chain') or '—'} · "
                f"next: {p.get('next_action') or '—'}"
            )
else:
    empty_state("No upcoming Farming / Waiting for TGE projects", "Advance stages on Project Tracker.")

# Airdrop deadlines
if with_deadline:
    with st.expander(f"Airdrop deadlines ({len(with_deadline)})", expanded=True):
        for a in with_deadline[:8]:
            status_badge(a.get("status") or "?", "warn")
            deadline = a.get("deadline") or "—"
            st.markdown(
                f"**{a.get('project_name', '—')}** · deadline `{deadline}` · "
                f"{a.get('chain') or '—'}"
            )
elif active_airdrops:
    st.caption(f"{len(active_airdrops)} active airdrops — no deadline fields set yet.")

# --- Portfolio summary ---
section_header("Portfolio", "Real holdings when rows exist — DEMO sample stays labelled")
price_map, px_source, px_live = provider.price_map()
if assets:
    summary = compute_summary(assets, price_map, is_live=px_live)
    data_mode_chip(summary["is_live"])
    st.caption(summary["source_note"] + f" · {px_source}")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        metric_card(f"${summary['total_value']:,.2f}", "Total value")
    with p2:
        metric_card(f"${summary['total_cost']:,.2f}", "Cost basis")
    with p3:
        pnl_kind = "up" if summary["total_pnl"] > 0 else "down" if summary["total_pnl"] < 0 else "flat"
        metric_card(
            f"${summary['total_pnl']:,.2f}",
            "Unrealized PnL",
            delta_kind=pnl_kind,
        )
    with p4:
        metric_card(str(len(assets)), f"Positions · {summary['unpriced_count']} unpriced")
    if summary["unpriced_count"]:
        st.caption("Some symbols lack prices — never invented.")
else:
    empty_state(
        "No portfolio assets yet",
        "Add holdings on the Portfolio page. DEMO sample below is labelled EXAMPLE only.",
    )
    with st.expander("Show labelled DEMO portfolio sample", expanded=False):
        demo_callout()
        folio = demo_portfolio_summary()
        st.caption(f"{folio['source']} · ${folio['total_usd']:,.0f}")
        df = pd.DataFrame(DEMO_PORTFOLIO)
        df["value_usd"] = df["amount"] * df["unit_value_usd"]
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- Notifications snippet ---
section_header("Notifications", "Unread inbox snippet")
if notifs:
    for n in notifs:
        title = (n.get("title") or "").replace("<", "&lt;").replace(">", "&gt;")
        cat = n.get("category", "general")
        created = n.get("created_at", "")
        st.markdown(
            f'<div class="mccc-card-dense"><span class="mccc-badge-warn">UNREAD</span> '
            f'<strong style="color:#e8eef5">{title}</strong>'
            f'<div style="color:#9aa7b5;font-size:0.78rem;margin-top:0.2rem">'
            f'{cat} · {created}</div></div>',
            unsafe_allow_html=True,
        )
    st.page_link("pages/15_Notifications.py", label="Open notifications", icon="🔔")
else:
    empty_state("No unread notifications", "Alerts and inbox items appear here when raised.")

# --- Announcements ---
section_header("Announcements", "Published product / research notes from local DB")
if announcements:
    for a in announcements:
        title = (a.get("title") or "").replace("<", "&lt;").replace(">", "&gt;")
        body = ((a.get("body") or "")[:280]).replace("<", "&lt;").replace(">", "&gt;")
        created = a.get("created_at", "")
        st.markdown(
            f'<div class="mccc-card"><span class="mccc-badge-info">NEWS</span> '
            f'<strong style="color:#e8eef5">{title}</strong>'
            f'<div style="color:#9aa7b5;font-size:0.82rem;margin-top:0.3rem">{body}</div>'
            f'<div style="color:#6a7785;font-size:0.72rem;margin-top:0.25rem">{created}</div></div>',
            unsafe_allow_html=True,
        )
else:
    empty_state(
        "No published announcements",
        "Admin / settings can publish announcements later — empty is OK.",
    )

# --- Partners strip ---
st.markdown(
    f'<div class="mccc-card"><span class="mccc-badge">PARTNERS</span>'
    f'<p style="margin:0.35rem 0 0;color:#e8eef5;"><strong>Platform Directory</strong> · {partner_count} active</p>'
    f'<p style="margin:0.15rem 0 0;color:#9aa7b5;font-size:0.85rem;">'
    f'Wallets, CEX, DEX, tools &amp; partners — open Partner Directory.</p></div>',
    unsafe_allow_html=True,
)
affiliate_disclosure_short()

# --- Research activity ---
section_header("Research activity", "Local usage / analytics (privacy-first, no PII)")
top_pages = usage.get("by_page") or []
r1, r2, r3 = st.columns(3)
with r1:
    metric_card(str(usage.get("total_events", 0)), "Total local events")
with r2:
    top = top_pages[0]["page_key"] if top_pages else "—"
    metric_card(str(top), "Top page")
with r3:
    metric_card(str(len(top_pages)), "Pages with views")
if top_pages:
    with st.expander("Page view breakdown", expanded=False):
        st.dataframe(
            pd.DataFrame(top_pages).rename(columns={"page_key": "page", "c": "views"}),
            use_container_width=True,
            hide_index=True,
        )

# --- Quick actions ---
section_header("Quick actions", "Jump to capture & research surfaces")
quick_actions()

# --- Security one-liner + disclosure ---
st.divider()
st.caption(f"🔒 {SEED_PHRASE_WARNING}")
st.caption(
    "Not financial advice. Research & education only. "
    "Official vs referral URLs stay separate — referrals are never hardcoded. "
    f"Local usage events: {usage.get('total_events', 0)}."
)
affiliate_disclosure_short()
footer("Command Center")
