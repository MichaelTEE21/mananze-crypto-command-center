"""Support MCCC — public BTC / ETH / SOL donation addresses + QR."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.donations import DONATION_WARNING, get_donation_channels, qr_png_bytes
from mccc.ui import error_banner, footer, hero, page_setup, seed_phrase_warning

page_setup("support_mccc", "Support MCCC")
hero(
    "Support MCCC",
    "Voluntary public donations help keep Mananze Crypto Command Center independent. "
    "Not a purchase of PRO. Not financial advice.",
)
seed_phrase_warning()
st.warning(DONATION_WARNING)

st.caption(
    "Addresses load from environment (`MCCC_*_DONATION_ADDRESS`) with documented public defaults. "
    "No donation totals are tracked or displayed here."
)

channels = get_donation_channels()
cols = st.columns(len(channels) or 1)

for col, ch in zip(cols, channels):
    with col:
        st.markdown(f"### {ch.asset}")
        st.markdown(f"**Network:** {ch.network}")
        st.markdown(f"**Asset:** {ch.asset}")
        st.code(ch.address, language=None)
        st.caption(
            f"Config: `{ch.env_key}` · "
            + ("from env" if ch.from_env else "documented default")
        )
        try:
            png = qr_png_bytes(ch.address)
            st.image(png, caption=f"QR encodes exact {ch.asset} address", use_container_width=True)
        except Exception as exc:  # noqa: BLE001
            error_banner(f"QR unavailable ({type(exc).__name__}). Address above is still valid — copy carefully.")
        st.link_button(f"Open {ch.network} explorer hub", ch.explorer_hint, use_container_width=True)

st.divider()
st.markdown(
    """
    ### What donations support
    - Keeping MCCC **independent** research tooling online
    - Hosting / infrastructure for the public Command Center
    - Continued **education**, Intelligence Report, and explorer work
    - **Not** a purchase of PRO, services, tokens, or investment products

    ### Verify before you send
    1. Confirm **network** matches the asset (BTC ≠ ETH ≠ SOL).
    2. Send a small test first if unsure.
    3. Never type a seed phrase, private key, or wallet password into MCCC or any “support” form.
    4. PRO unlocks are **not** sold via donation — see PRO Architecture.
    """
)
st.page_link("pages/10_PRO_Architecture.py", label="PRO Architecture (payments Coming Soon)", icon="⭐")
st.page_link("pages/29_About.py", label="About MCCC", icon="ℹ️")

footer("Support MCCC · thank you")
