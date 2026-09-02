"""About MCCC — lightweight."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc import APP_NAME, APP_TAGLINE, __version__
from mccc.ui import footer, hero, page_setup

page_setup("about", "About")
hero("About MCCC", f"{APP_NAME} · v{__version__}")

st.markdown(
    f"""
    ## {APP_TAGLINE}

    **Understand Crypto. Read the Chain. Learn as You Go.**

    Mananze Crypto Command Center (MCCC) is a **Streamlit research OS** for crypto diligence:
    search, analyse, learn, monitor, and act — without custodial wallets or invented chain data.

    ### What MCCC is
    - Local-first / privacy-aware command center for research notes, trackers, and labelled market data
    - Public-address wallet tracking only
    - Education + Intelligence Reports grounded in retrieved sources when available

    ### What MCCC is not
    - Not a bank, exchange, broker, or custodian
    - Not financial advice
    - Not a place to paste seed phrases or private keys

    ### Honesty labels
    - **LIVE** vs **DEMO** for market / sample data
    - **VERIFIED** / **CALCULATED** / **INFERENCE** / **DATA UNAVAILABLE** for analyst & explorer output

    Built for **B=MananzeZA**. Technocore is a separate product.
    """
)
st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon="💜")
st.page_link("pages/30_Privacy.py", label="Privacy", icon="🔒")
st.page_link("pages/31_Terms.py", label="Terms", icon="📜")

footer("About")
