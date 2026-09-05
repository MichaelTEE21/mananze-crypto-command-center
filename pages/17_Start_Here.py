"""Beginner onboarding + partner wallet/CEX links."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.partners import list_partner_links
from mccc.ui import (
    render_support_cta_banner,
    footer,
    affiliate_disclosure,
    empty_state,
    hero,
    page_setup,
    partner_cta,
    seed_phrase_warning,
)

page_setup("start_here", "Start Here")
hero(
    "Start Crypto",
    "Beginner journey — security first, then Academy, explorers, trackers. Understand Crypto. Read the Chain. Learn as You Go.",
)

st.markdown(
    """
    ## Welcome to the Command Center

    MCCC is a **local research OS** for crypto diligence — not a custodian, exchange, or broker.

    ### Golden rules
    1. **Never** enter seed phrases or private keys anywhere in MCCC.
    2. Treat DEMO / EXAMPLE data as practice — never as live balances or eligibility.
    3. Prefer primary sources (docs, explorers, audits) over screenshots.
    4. Partner / referral links may earn MCCC compensation at **no extra cost to you**.
    """
)
seed_phrase_warning()
affiliate_disclosure()

st.subheader("Suggested path")
steps = [
    ("📚 Academy", "pages/8_Education.py", "Read wallet + security lessons first"),
    ("🔗 Explorers", "pages/32_Chain_Explorers.py", "Public address / tx lookup — UNAVAILABLE when no provider"),
    ("🛰️ Intelligence", "pages/24_Intelligence_Center.py", "Analyse → Intelligence Report (grounded)"),
    ("👤 Account", "pages/16_Account.py", "Optional local profile"),
    ("💼 Portfolio", "pages/13_Portfolio.py", "Track cost basis (manual)"),
    ("📁 Projects", "pages/2_Project_Tracker.py", "Statuses: DISCOVERED → RESEARCHING → … (no fake claims)"),
    ("⭐ Watchlist", "pages/14_Watchlist.py", "Rules you define — no fabricated alert firings"),
    ("🪂 Airdrops", "pages/3_Airdrop_Tracker.py", "Eligibility notes — not claims"),
    ("📈 Markets", "pages/1_Markets.py", "Live or labelled DEMO prices"),
    ("💜 Support MCCC", "pages/28_Support_MCCC.py", "Optional public donations"),
]
for label, path, hint in steps:
    cols = st.columns((2, 3))
    with cols[0]:
        st.page_link(path, label=label)
    with cols[1]:
        st.caption(hint)

st.divider()
st.subheader("Approved wallets & CEX (Partner Directory)")
st.caption("Links resolve via partners.resolve — never hardcoded referral URLs in this page.")

for cat, title in [("Wallets", "Wallets"), ("CEX", "Centralized exchanges")]:
    st.markdown(f"### {title}")
    links = list_partner_links(status="Active", category=cat)
    if not links:
        empty_state(f"No active {cat} listings", "Add via Admin Partner Links.")
    else:
        for link in links:
            st.markdown(f"**{link['name']}**")
            if link.get("description"):
                st.write(link["description"])
            if link.get("official_url"):
                st.caption(f"Official (verify): {link['official_url']}")
            partner_cta(link, key_prefix=f"start_{cat.lower()}", source_page="start_here")
            st.divider()

st.info("Not financial advice. Do your own research. MCCC will never ask for your seed phrase.")

render_support_cta_banner(compact=True)
footer("Start Here")
