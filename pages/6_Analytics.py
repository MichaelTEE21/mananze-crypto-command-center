"""Stage 6 — Analytics charts (Plotly) on demo or fetched data."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

from mccc.db import is_feature_enabled
from mccc.demo_data import DEMO_PORTFOLIO, DEMO_PRICE_HISTORY, portfolio_summary
from mccc.market import fetch_prices
from mccc.ui import demo_callout, hero, page_setup, pro_locked_panel

page_setup("analytics", "Analytics")
hero("Analytics", "Simple charts on labelled DEMO series and/or live market snapshot.")

prices, source, is_live = fetch_prices()
if is_live:
    st.success(f"Market bars source: {source}")
else:
    demo_callout(f"Market bars source: {source}")

pdf = pd.DataFrame(prices)
if not pdf.empty:
    fig = px.bar(
        pdf,
        x="symbol",
        y="current_price",
        color="symbol",
        title=f"Price snapshot ({'LIVE' if is_live else 'DEMO'})",
        labels={"current_price": "USD", "symbol": "Asset"},
        template="plotly_dark",
    )
    fig.update_layout(paper_bgcolor="#0b0f14", plot_bgcolor="#141a22", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("DEMO price history (30d synthetic)")
demo_callout("These series are EXAMPLE / synthetic — not historical live candles.")
asset = st.selectbox("DEMO series", list(DEMO_PRICE_HISTORY.keys()))
hist = pd.DataFrame(DEMO_PRICE_HISTORY[asset])
line = px.line(hist, x="day", y="price", title=f"{asset} DEMO trajectory", template="plotly_dark")
line.update_layout(paper_bgcolor="#0b0f14", plot_bgcolor="#141a22")
st.plotly_chart(line, use_container_width=True)

st.subheader("DEMO portfolio allocation")
folio = pd.DataFrame(DEMO_PORTFOLIO)
folio["value"] = folio["amount"] * folio["unit_value_usd"]
pie = px.pie(folio, names="asset", values="value", title=f"DEMO portfolio · ${portfolio_summary()['total_usd']:,.0f}", template="plotly_dark")
pie.update_layout(paper_bgcolor="#0b0f14")
st.plotly_chart(pie, use_container_width=True)

st.divider()
st.subheader("PRO advanced analytics (architecture)")
if is_feature_enabled("pro_advanced_analytics"):
    st.success("PRO flag unlocked locally — showing extra DEMO correlation table.")
    corr = hist.assign(ret=hist["price"].pct_change()).dropna()
    st.dataframe(corr.tail(10), use_container_width=True, hide_index=True)
else:
    pro_locked_panel("Multi-series analytics & export")
