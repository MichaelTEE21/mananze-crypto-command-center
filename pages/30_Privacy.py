"""Privacy — lightweight."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.ui import footer, hero, page_setup, seed_phrase_warning

page_setup("privacy", "Privacy")
hero("Privacy", "What MCCC stores — and what it refuses.")
seed_phrase_warning()

st.markdown(
    """
    ## Summary

    - **App accounts** (optional): email, scrypt password hash, display prefs — local SQLite (or host volume).
    - **Research data**: projects, airdrops, public wallet addresses, notes, watchlists — on the configured DB path.
    - **Usage events**: coarse page/feature counters — no IP scraping for partner clicks.
    - **Never stored:** seed phrases, private keys, wallet/exchange passwords, 2FA secrets.

    Guest mode works without an account. Soft-delete scrubs account secrets.

    Hosted deployments may use a persistent disk (`MCCC_DATA_DIR`). Operators of a shared host
    can see that disk — treat self-host credentials accordingly.

    Third-party APIs (CoinGecko, Etherscan, optional LLM) receive only the queries you trigger —
    never seeds. See Security notes in `docs/SECURITY.md`.
    """
)
st.page_link("pages/31_Terms.py", label="Terms", icon="📜")
footer("Privacy")
