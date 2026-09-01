"""Stage 5 — Market APIs (CoinGecko + DEMO fallback)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.market import DEFAULT_IDS, fetch_prices
from mccc.ui import demo_callout, hero, page_setup

page_setup("market_apis", "Market APIs")
hero("Market APIs", "Prices from CoinGecko public API when reachable; otherwise labelled DEMO table.")

ids = st.text_input("CoinGecko ids (comma-separated)", value=DEFAULT_IDS)
if st.button("Refresh prices", type="primary"):
    st.session_state["mccc_force_fetch"] = True

prices, source, is_live = fetch_prices(ids=ids.strip() or DEFAULT_IDS)
if is_live:
    st.success(f"Source: {source}")
else:
    demo_callout(f"Source: {source}")

df = pd.DataFrame(prices)
if not df.empty:
    show = df.copy()
    show["market_cap"] = show["market_cap"].apply(lambda x: f"{x:,.0f}" if x is not None else "—")
    show = show.rename(columns={
        "symbol": "Symbol",
        "name": "Name",
        "current_price": "Price (USD)",
        "price_change_percentage_24h": "24h %",
        "market_cap": "Market cap",
        "id": "ID",
    })
    st.dataframe(show, use_container_width=True, hide_index=True)
else:
    st.warning("No rows returned.")

st.caption("Optional COINGECKO_API_KEY in .env — never commit secrets. Offline → DEMO fallback.")
