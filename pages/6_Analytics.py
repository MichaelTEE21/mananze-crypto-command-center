"""Stage 6 — Analytics charts (Plotly) on demo or fetched data."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

from mccc.subscriptions import has_pro_feature
from mccc.demo_data import DEMO_PORTFOLIO, DEMO_PRICE_HISTORY, portfolio_summary
from mccc.portfolio import list_assets, compute_summary
from mccc.market_provider import get_default_provider
from mccc.ui import demo_callout, footer, hero, page_setup, pro_locked_panel, session_user_id, upgrade_cta

page_setup("analytics", "Analytics")
hero("Analytics", "Simple charts on labelled DEMO series and/or live market snapshot.")

prices, source, is_live = get_default_provider().get_prices()
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

st.subheader("Portfolio allocation")
assets = list_assets(user_id=session_user_id())
if assets:
    price_map, _, px_live = get_default_provider().price_map()
    summary = compute_summary(assets, price_map, is_live=px_live)
    pos = [p for p in summary["positions"] if p.get("value")]
    if pos:
        folio = pd.DataFrame(pos)
        pie = px.pie(
            folio, names="symbol", values="value",
            title=f"Portfolio · ${summary['total_value']:,.0f} ({'LIVE' if summary['is_live'] else 'DEMO prices'})",
            template="plotly_dark",
        )
        pie.update_layout(paper_bgcolor="#0b0f14")
        st.plotly_chart(pie, use_container_width=True)
    else:
        demo_callout("Positions exist but lack priced values — showing DEMO sample.")
        folio = pd.DataFrame(DEMO_PORTFOLIO)
        folio["value"] = folio["amount"] * folio["unit_value_usd"]
        pie = px.pie(folio, names="asset", values="value", title=f"DEMO portfolio · ${portfolio_summary()['total_usd']:,.0f}", template="plotly_dark")
        pie.update_layout(paper_bgcolor="#0b0f14")
        st.plotly_chart(pie, use_container_width=True)
else:
    demo_callout("No portfolio assets — DEMO allocation sample only.")
    folio = pd.DataFrame(DEMO_PORTFOLIO)
    folio["value"] = folio["amount"] * folio["unit_value_usd"]
    pie = px.pie(folio, names="asset", values="value", title=f"DEMO portfolio · ${portfolio_summary()['total_usd']:,.0f}", template="plotly_dark")
    pie.update_layout(paper_bgcolor="#0b0f14")
    st.plotly_chart(pie, use_container_width=True)

st.divider()
st.subheader("PRO advanced analytics & export")
_uid = session_user_id()
if has_pro_feature("pro_advanced_analytics", user_id=_uid):
    st.success("PRO unlocked locally — advanced DEMO correlation + CSV export.")
    corr = hist.assign(ret=hist["price"].pct_change()).dropna()
    st.dataframe(corr.tail(10), use_container_width=True, hide_index=True)
    csv = corr.to_csv(index=False)
    st.download_button(
        "Export DEMO series CSV (PRO)",
        data=csv,
        file_name="mccc_demo_analytics_export.csv",
        mime="text/csv",
    )
    st.caption("Export is local DEMO/synthetic series unless markets are LIVE — labelled honestly.")
else:
    pro_locked_panel("Multi-series analytics & export")
    upgrade_cta("Advanced analytics export requires PRO (Coming Soon payments).")


st.divider()
st.subheader("RWA analytics (stored profiles)")
try:
    from mccc.intelligence.rwa.service import RWAService

    rwa_summary = RWAService().analytics()
    if rwa_summary.get("demo"):
        demo_callout(f"RWA data mode: {rwa_summary.get('data_mode')} — DEMO seeds labelled.")
    c1, c2, c3 = st.columns(3)
    c1.metric("RWA profiles", rwa_summary.get("total", 0))
    c2.metric("DEMO", rwa_summary.get("demo", 0))
    c3.metric("Live", rwa_summary.get("live", 0))
    if rwa_summary.get("by_category"):
        cdf = pd.DataFrame(
            [{"category": k, "count": v} for k, v in rwa_summary["by_category"].items()]
        )
        fig_rwa = px.bar(
            cdf, x="category", y="count",
            title="RWA profiles by category (stored)",
            template="plotly_dark",
        )
        fig_rwa.update_layout(paper_bgcolor="#0b0f14", plot_bgcolor="#141a22")
        st.plotly_chart(fig_rwa, use_container_width=True)
    st.page_link("pages/25_RWA_Intelligence.py", label="Open RWA Intelligence", icon="🏛️")
except Exception as exc:  # noqa: BLE001
    st.caption(f"RWA analytics unavailable: {exc}")

footer("Analytics")
