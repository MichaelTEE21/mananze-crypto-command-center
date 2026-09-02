"""Market APIs — slim CoinGecko tinkering page (rich UI lives on Markets)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.market import DEFAULT_IDS
from mccc.market_provider import clear_market_cache, get_default_provider
from mccc.ui import demo_callout, hero, live_or_demo_badge, page_setup, footer

page_setup("market_apis", "Market APIs")
hero(
    "Market APIs",
    "Slim API workspace. Prefer **Markets** for the full overview. DEMO fallback is labelled.",
)

st.page_link("pages/1_Markets.py", label="Open Markets (rich)", icon="📈")
st.caption("This page remains for raw id experiments and cache control.")

provider = get_default_provider()
ids = st.text_input("CoinGecko ids (comma-separated)", value=DEFAULT_IDS)
c1, c2 = st.columns(2)
with c1:
    refresh = st.button("Refresh prices", type="primary", use_container_width=True)
with c2:
    if st.button("Clear TTL cache", use_container_width=True):
        clear_market_cache()
        st.success("Cache cleared.")

if refresh:
    clear_market_cache()

prices, source, is_live = provider.get_prices(ids=ids.strip() or DEFAULT_IDS)
live_or_demo_badge(is_live)
if is_live:
    st.success(f"Source: {source}")
else:
    demo_callout(f"Source: {source}")

df = pd.DataFrame(prices)
if not df.empty:
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
else:
    st.warning("No rows returned.")

st.caption("Optional COINGECKO_API_KEY in .env — never commit secrets. Offline → DEMO fallback.")

footer("Market APIs")
