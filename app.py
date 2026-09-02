"""
MANANZE CRYPTO COMMAND CENTER (MCCC)
Entry point — premium Command Center cockpit.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from mccc import APP_NAME, APP_TAGLINE, __version__
from mccc.db import init_db, list_airdrops, list_projects, list_wallets, usage_summary
from mccc.demo_data import DEMO_PORTFOLIO, portfolio_summary as demo_portfolio_summary
from mccc.market_provider import get_default_provider
from mccc.partners import list_partner_links
from mccc.portfolio import compute_summary, list_assets
from mccc.ui import (
    affiliate_disclosure_short,
    demo_callout,
    empty_state,
    hero,
    live_or_demo_badge,
    metric_card,
    page_setup,
    session_user_id,
)
from mccc.watchlist import list_items as list_watchlist

page_setup("command_center", "Command Center")

hero(
    APP_NAME,
    f"{APP_TAGLINE} · local research OS · v{__version__}",
)

init_db()
uid = session_user_id()
provider = get_default_provider()

# --- Market overview ---
st.subheader("Market overview")
overview, ov_source, ov_live = provider.get_overview()
live_or_demo_badge(ov_live)
st.caption(f"Source: {ov_source}")
if not ov_live:
    demo_callout("Market overview is DEMO / incomplete — not live market quotes.")

def _px(coin: dict | None) -> str:
    if not coin or coin.get("current_price") is None:
        return "—"
    try:
        return f"${float(coin['current_price']):,.2f}"
    except (TypeError, ValueError):
        return "—"

def _chg(coin: dict | None) -> str:
    if not coin or coin.get("price_change_percentage_24h") is None:
        return "—"
    try:
        return f"{float(coin['price_change_percentage_24h']):+.2f}%"
    except (TypeError, ValueError):
        return "—"

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    metric_card(_px(overview.get("btc")), f"BTC · {_chg(overview.get('btc'))}")
with m2:
    metric_card(_px(overview.get("eth")), f"ETH · {_chg(overview.get('eth'))}")
with m3:
    metric_card(_px(overview.get("sol")), f"SOL · {_chg(overview.get('sol'))}")
with m4:
    mcap = overview.get("total_market_cap_usd")
    metric_card(f"${mcap/1e12:.2f}T" if mcap else "—", "Total mcap")
with m5:
    dom = overview.get("btc_dominance")
    eth_dom = overview.get("eth_dominance")
    dom_s = f"{dom:.1f}%" if isinstance(dom, (int, float)) else "—"
    eth_s = f"{eth_dom:.1f}%" if isinstance(eth_dom, (int, float)) else "—"
    metric_card(dom_s, f"BTC dom · ETH {eth_s}")

st.caption("Fear & Greed: unavailable (no reliable free API wired).")

# --- Portfolio summary ---
st.subheader("Portfolio")
assets = list_assets(user_id=uid)
price_map, px_source, px_live = provider.price_map()
if assets:
    summary = compute_summary(assets, price_map, is_live=px_live)
    live_or_demo_badge(summary["is_live"])
    st.caption(summary["source_note"] + f" · {px_source}")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        metric_card(f"${summary['total_value']:,.2f}", "Total value")
    with p2:
        metric_card(f"${summary['total_cost']:,.2f}", "Cost basis")
    with p3:
        metric_card(f"${summary['total_pnl']:,.2f}", "Unrealized PnL")
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

# --- Snapshots ---
projects = list_projects()
airdrops = list_airdrops()
wallets = list_wallets()
watch = list_watchlist(user_id=uid)
usage = usage_summary()
partner_count = len(list_partner_links(status="Active"))

st.subheader("Research snapshots")
s1, s2, s3, s4 = st.columns(4)
with s1:
    metric_card(str(len(projects)), "Projects")
with s2:
    metric_card(str(len(airdrops)), "Airdrops")
with s3:
    metric_card(str(len(wallets)), "Watch wallets")
with s4:
    metric_card(str(len(watch)), "Watchlist items")

st.markdown(
    f'<div class="mccc-card"><span class="mccc-badge">PARTNERS</span>'
    f'<p style="margin:0.35rem 0 0;color:#e8eef5;"><strong>Platform Directory</strong> · {partner_count} active</p>'
    f'<p style="margin:0.15rem 0 0;color:#9aa7b5;font-size:0.85rem;">'
    f'Wallets, CEX, DEX, tools &amp; partners — open Partner Directory. </p></div>',
    unsafe_allow_html=True,
)
affiliate_disclosure_short()

st.divider()
st.subheader("Quick actions")
qa = st.columns(4)
with qa[0]:
    st.page_link("pages/17_Start_Here.py", label="Start Here", icon="🚀")
    st.page_link("pages/1_Markets.py", label="Markets", icon="📈")
    st.page_link("pages/13_Portfolio.py", label="Portfolio", icon="💼")
with qa[1]:
    st.page_link("pages/2_Project_Tracker.py", label="Projects", icon="📁")
    st.page_link("pages/3_Airdrop_Tracker.py", label="Airdrops", icon="🪂")
    st.page_link("pages/4_Wallet_Tracking.py", label="Wallets", icon="👀")
with qa[2]:
    st.page_link("pages/14_Watchlist.py", label="Watchlist", icon="⭐")
    st.page_link("pages/15_Notifications.py", label="Notifications", icon="🔔")
    st.page_link("pages/18_Search.py", label="Search", icon="🔍")
with qa[3]:
    st.page_link("pages/7_AI_Assistant.py", label="AI Assistant", icon="🤖")
    st.page_link("pages/8_Education.py", label="Education", icon="📚")
    st.page_link("pages/16_Account.py", label="Account", icon="👤")

st.divider()
st.caption(
    "Not financial advice. Research & education only. MCCC never asks for seed phrases or private keys. "
    f"Local usage events: {usage['total_events']}."
)
affiliate_disclosure_short()
