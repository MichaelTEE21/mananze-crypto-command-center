"""Markets — rich market overview via market_provider."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.market import DEFAULT_IDS
from mccc.market_provider import clear_market_cache, get_default_provider
from mccc.ui import demo_callout, empty_state, hero, live_or_demo_badge, metric_card, page_setup, footer

page_setup("markets", "Markets")
hero("Markets", "BTC / ETH / SOL + CoinGecko markets. DEMO fallback is always labelled.")

provider = get_default_provider()

c_top = st.columns((3, 1))
with c_top[1]:
    if st.button("Refresh (clear cache)", use_container_width=True):
        clear_market_cache()
        st.rerun()

overview, ov_source, ov_live = provider.get_overview()
live_or_demo_badge(ov_live)
st.caption(f"Overview source: {ov_source}")
if not ov_live:
    demo_callout()

def _fmt_px(coin):
    if not coin or coin.get("current_price") is None:
        return "—"
    return f"${float(coin['current_price']):,.4g}"

def _fmt_chg(coin):
    if not coin or coin.get("price_change_percentage_24h") is None:
        return "—"
    return f"{float(coin['price_change_percentage_24h']):+.2f}%"

a, b, c, d, e = st.columns(5)
with a:
    metric_card(_fmt_px(overview.get("btc")), f"Bitcoin · {_fmt_chg(overview.get('btc'))}")
with b:
    metric_card(_fmt_px(overview.get("eth")), f"Ethereum · {_fmt_chg(overview.get('eth'))}")
with c:
    metric_card(_fmt_px(overview.get("sol")), f"Solana · {_fmt_chg(overview.get('sol'))}")
with d:
    mcap = overview.get("total_market_cap_usd")
    metric_card(f"${mcap:,.0f}" if mcap else "—", "Total market cap")
with e:
    dom = overview.get("btc_dominance")
    metric_card(f"{dom:.2f}%" if isinstance(dom, (int, float)) else "—", "BTC dominance")

st.caption("Fear & Greed index: unavailable.")

st.subheader("Coin markets")
ids = st.text_input("CoinGecko ids (comma-separated)", value=DEFAULT_IDS)
rows, source, is_live = provider.get_prices(ids=ids.strip() or DEFAULT_IDS)
live_or_demo_badge(is_live)
if is_live:
    st.success(f"Source: {source}")
else:
    demo_callout(f"Source: {source}")

if not rows:
    empty_state("No market rows", "Check network or ids, then refresh.")
else:
    df = pd.DataFrame(rows)
    show = df.copy()
    if "market_cap" in show.columns:
        show["market_cap"] = show["market_cap"].apply(lambda x: f"{x:,.0f}" if x is not None else "—")
    show = show.rename(
        columns={
            "symbol": "Symbol",
            "name": "Name",
            "current_price": "Price (USD)",
            "price_change_percentage_24h": "24h %",
            "market_cap": "Market cap",
            "id": "ID",
        }
    )
    st.dataframe(show, use_container_width=True, hide_index=True)

st.info("For raw API tinkering see **Market APIs** (stage 5). Prices are never silently invented.")
st.page_link("pages/26_Tokens.py", label="Token Intelligence", icon="🪙")
st.page_link("pages/5_Market_APIs.py", label="Open Market APIs (slim)", icon="🔌")

footer("Markets")
