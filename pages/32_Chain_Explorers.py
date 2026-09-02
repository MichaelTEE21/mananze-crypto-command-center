"""Chain explorers — modular providers; UNAVAILABLE when no real source."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.explorers import DATA_UNAVAILABLE, available_chains, list_providers, lookup_address, lookup_tx
from mccc.ui import error_banner, footer, hero, page_setup, seed_phrase_warning, status_badge

page_setup("chain_explorers", "Chain Explorers")
hero(
    "Chain Explorers",
    "Wallet + transaction lookup via modular providers. "
    "Only chains with real providers return data — otherwise DATA UNAVAILABLE.",
)
seed_phrase_warning()

st.info(
    "Labels: **VERIFIED** (sourced) · **CALCULATED** (derived from retrieved fields) · "
    "**INFERENCE** (explicit opinion) · **UNAVAILABLE** / **DEMO**."
)

providers = list_providers()
st.caption(
    "Registered: "
    + ", ".join(f"{p.display_name} (`{p.chain}`)" + (" ✓" if p.available() else " ✗") for p in providers)
)
st.caption(f"Available now: {', '.join(available_chains()) or 'none'}")

kind = st.radio("Lookup", ["Address / wallet", "Transaction"], horizontal=True)
chain = st.selectbox("Chain", [p.chain for p in providers], format_func=lambda c: next(
    (p.display_name for p in providers if p.chain == c), c
))
query = st.text_input("Public address or tx hash", placeholder="Never paste seeds or private keys")

if st.button("Lookup", type="primary"):
    if not query.strip():
        st.warning("Enter a public address or transaction id.")
    else:
        try:
            result = (
                lookup_address(chain, query.strip())
                if kind.startswith("Address")
                else lookup_tx(chain, query.strip())
            )
            kind_map = {
                "VERIFIED": "success",
                "CALCULATED": "info",
                "INFERENCE": "warn",
                "DEMO": "warn",
                "UNAVAILABLE": "danger",
            }
            status_badge(result.label or result.status.value, kind_map.get(result.label, "info"))
            st.write(result.summary)
            st.caption(f"Source: {result.source}")
            if result.fields:
                st.json(result.fields)
            if result.label == "UNAVAILABLE" or result.summary.startswith(DATA_UNAVAILABLE):
                st.info("No invented balances or txs — try another chain or set required API keys.")
        except Exception:  # noqa: BLE001
            error_banner("Lookup failed. Try again — no raw stack trace shown.")

footer("Chain Explorers")
