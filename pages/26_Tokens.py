"""Token Intelligence — market foundation; holders/tokenomics/locks UNAVAILABLE until Phase 2."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.token_intel import DATA_UNAVAILABLE, build_token_market_snapshot, format_money
from mccc.ui import (
    data_mode_chip,
    demo_callout,
    empty_state,
    footer,
    hero,
    metric_card,
    page_setup,
    section_header,
)

page_setup("tokens", "Tokens")
hero(
    "TOKEN INTELLIGENCE",
    "Market fields from providers when available · never invent tokenomics / locks / holders",
)
st.caption("Research only — not financial advice. Distinguish FACT / VERIFIED / UNAVAILABLE.")
st.page_link("pages/24_Intelligence_Center.py", label="ANALYSE token in Intelligence Report", icon="🛰️")
st.page_link("pages/1_Markets.py", label="Open Markets overview", icon="📈")

q = st.text_input(
    "Token",
    value=st.session_state.get("mccc_token_q", "bitcoin"),
    placeholder="$BTC · ethereum · sol · usd-coin",
).strip().lstrip("$")
st.session_state["mccc_token_q"] = q

if not q:
    empty_state("Enter a token id or symbol", "Uses CoinGecko ids when reachable; DEMO labelled otherwise.")
    footer("Tokens")
    st.stop()

if st.button("Load token snapshot", type="primary") or q:
    snap = build_token_market_snapshot(q)
    prov = snap.provenance
    if prov:
        data_mode_chip(prov.is_live)
        st.caption(
            f"Source: {prov.source} · last updated: {prov.last_updated} · "
            f"data quality: {prov.data_quality}"
        )
        if prov.is_demo or not prov.is_live:
            demo_callout("Market rows may be DEMO / incomplete — not silent live quotes.")

    section_header("Market", "Price · mcap · FDV · volume when present in provider response")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(format_money(snap.price_usd) if snap.price_usd is not None else DATA_UNAVAILABLE, f"{snap.symbol or snap.token_id} price")
    with c2:
        metric_card(format_money(snap.market_cap_usd), "Market cap")
    with c3:
        metric_card(format_money(snap.fdv_usd), "FDV")
    with c4:
        metric_card(format_money(snap.volume_24h_usd), "24h volume")

    section_header("Supply (sourced only)", "Never invent circulating / total / max supply")
    s1, s2, s3 = st.columns(3)
    with s1:
        metric_card(
            f"{snap.circulating_supply:,.0f}" if isinstance(snap.circulating_supply, (int, float)) else DATA_UNAVAILABLE,
            "Circulating",
        )
    with s2:
        metric_card(
            f"{snap.total_supply:,.0f}" if isinstance(snap.total_supply, (int, float)) else DATA_UNAVAILABLE,
            "Total supply",
        )
    with s3:
        metric_card(
            f"{snap.max_supply:,.0f}" if isinstance(snap.max_supply, (int, float)) else DATA_UNAVAILABLE,
            "Max supply",
        )

    section_header("Holders / tokenomics / locks", "Phase 2 data — placeholders only")
    st.info(
        f"**Holders:** {snap.holders_status}  \n"
        f"**Tokenomics breakdown:** {snap.tokenomics_status}  \n"
        f"**Locks / vesting:** {snap.locks_status} / {snap.vesting_status}"
    )
    for n in snap.notes:
        st.caption(f"· {n}")

    if st.button("ANALYSE in Intelligence Report", key="token_analyse"):
        st.session_state["intel_report_q"] = snap.token_id or q
        st.session_state["mccc_analyse_entity_hint"] = "token"
        st.switch_page("pages/24_Intelligence_Center.py")

footer("Tokens")
