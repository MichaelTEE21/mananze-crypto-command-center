"""
MANANZE CRYPTO COMMAND CENTER (MCCC)
Entry point — Stage 1 Command Center shell + navigation hub.
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
from mccc.demo_data import DEMO_PORTFOLIO, portfolio_summary
from mccc.market import fetch_prices
from mccc.ui import demo_callout, hero, inject_css, page_setup

page_setup("command_center", "Command Center")

hero(
    APP_NAME,
    f"{APP_TAGLINE} · local OS for research · v{__version__}",
    show_demo_banner=True,
)

init_db()

# Overview metrics
projects = list_projects()
airdrops = list_airdrops()
wallets = list_wallets()
usage = usage_summary()
folio = portfolio_summary()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="mccc-card"><div class="mccc-metric">' + str(len(projects)) + '</div>Research projects</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="mccc-card"><div class="mccc-metric">' + str(len(airdrops)) + '</div>Airdrops tracked</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="mccc-card"><div class="mccc-metric">' + str(len(wallets)) + '</div>Watch addresses</div>', unsafe_allow_html=True)
with c4:
    st.markdown(
        f'<div class="mccc-card"><div class="mccc-metric">${folio["total_usd"]:,.0f}</div>'
        f'DEMO portfolio · {folio["source"]}</div>',
        unsafe_allow_html=True,
    )

demo_callout()

left, right = st.columns((1.2, 1))

with left:
    st.subheader("DEMO portfolio positions")
    df = pd.DataFrame(DEMO_PORTFOLIO)
    df["value_usd"] = df["amount"] * df["unit_value_usd"]
    st.dataframe(
        df.rename(columns={
            "asset": "Asset (DEMO)",
            "amount": "Amount",
            "unit_value_usd": "Unit USD (DEMO)",
            "note": "Note",
            "value_usd": "Value USD (DEMO)",
        }),
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.subheader("Market snapshot")
    prices, source, is_live = fetch_prices()
    if is_live:
        st.success(f"Live source: {source}")
    else:
        st.info(f"Source: {source}")
    pdf = pd.DataFrame(prices)[["symbol", "name", "current_price", "price_change_percentage_24h"]]
    pdf.columns = ["Symbol", "Name", "Price", "24h %"]
    st.dataframe(pdf, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Navigate the OS")
nav_cols = st.columns(5)
links = [
    ("📁 Project Tracker", "pages/2_Project_Tracker.py"),
    ("🪂 Airdrop Tracker", "pages/3_Airdrop_Tracker.py"),
    ("👀 Wallet Tracking", "pages/4_Wallet_Tracking.py"),
    ("📈 Market APIs", "pages/5_Market_APIs.py"),
    ("📊 Analytics", "pages/6_Analytics.py"),
]
# Streamlit multipage uses sidebar; show guidance cards
stages = [
    ("01", "Command Center", "This hub — overview & DEMO portfolio"),
    ("02", "Project Tracker", "SQLite research cases & notes"),
    ("03", "Airdrop Tracker", "Eligibility notes & statuses"),
    ("04", "Wallet Tracking", "Public addresses only"),
    ("05", "Market APIs", "CoinGecko + DEMO fallback"),
    ("06", "Analytics", "Plotly charts on labelled data"),
    ("07", "AI Assistant", "Rule-based research checklists"),
    ("08", "Education", "Markdown lessons"),
    ("09", "User Analytics", "Local usage stats"),
    ("10", "PRO Architecture", "Feature flags & paywall mock"),
]
cols = st.columns(2)
for i, (num, name, desc) in enumerate(stages):
    with cols[i % 2]:
        st.markdown(
            f'<div class="mccc-card"><span class="mccc-badge">STAGE {num}</span>'
            f'<p style="margin:0.4rem 0 0;color:#e8eef5;"><strong>{name}</strong></p>'
            f'<p style="margin:0.2rem 0 0;color:#9aa7b5;font-size:0.9rem;">{desc}</p></div>',
            unsafe_allow_html=True,
        )

st.caption(f"Usage events logged locally: {usage['total_events']} · Use the sidebar to open stages.")
