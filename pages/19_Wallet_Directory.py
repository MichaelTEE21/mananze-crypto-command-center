"""Wallet Directory — educational listings only. Never collect credentials."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import init_db
from mccc.partners import list_partner_links
from mccc.paths import EDUCATION_DIR
from mccc.ui import (
    footer,
    affiliate_disclosure,
    referral_leave_disclosure,
    empty_state,
    hero,
    page_setup,
    partner_cta,
    section_header,
    seed_phrase_warning,
)

page_setup("wallet_directory", "Wallet Hub")
hero(
    "Wallet Hub",
    "Educational wallet listings from central Partner Links — research only. MCCC never asks for seeds or keys.",
    show_demo_banner=True,
)

init_db()
affiliate_disclosure()
referral_leave_disclosure()
seed_phrase_warning()

st.error(
    "SECURITY: This page never collects seed phrases, private keys, passwords, or 2FA secrets. "
    "Use Partner Directory visit links only after verifying the official URL yourself."
)

section_header("Learn Before You Connect", "Read these lessons before installing or connecting any wallet")
LESSON_KEYS = [
    ("seed_phrase", "Seed phrases"),
    ("private_key", "Private keys"),
    ("key_safety", "Key safety"),
    ("wallet_security", "Wallet security"),
    ("wallet", "Wallet basics"),
    ("phishing", "Phishing"),
]
edu_cols = st.columns(3)
for i, (stem, label) in enumerate(LESSON_KEYS):
    path = EDUCATION_DIR / f"{stem}.md"
    with edu_cols[i % 3]:
        if path.exists():
            st.page_link("pages/8_Education.py", label=f"📘 {label}", help=f"Open Education · {stem}")
            st.caption(f"`{stem}.md`")
        else:
            st.caption(f"{label} (lesson missing)")

st.info(
    "Public addresses are safe to watch on **Wallet Tracking**. "
    "Never type recovery phrases into any website — including this app."
)

# Static educational tips (not product endorsements)
section_header("Self-custody checklist (educational)", "Static guidance — not a recommendation of any vendor")
st.markdown(
    """
1. Download wallet software only from the **official** site you typed yourself (bookmark it).
2. Write your seed on paper offline — never screenshot, never cloud notes, never paste here.
3. Verify URLs character-by-character; watch for lookalike domains.
4. Start with a small test transfer before moving meaningful funds.
5. DEMO directory rows below are labelled and use `example.com` or disclosed partners.
"""
)

section_header("Partner directory — Wallets", "Active Wallets category from the central Partner Links DB")
wallets = list_partner_links(status="Active", category="Wallets")
if not wallets:
    empty_state(
        "No Active Wallets partners yet",
        "Admin can add Wallets category rows on Admin Partner Links. DEMO seeds appear on first launch.",
    )
else:
    for link in wallets:
        with st.container():
            badge = "REFERRAL" if (link.get("referral_url") or "").strip() else "OFFICIAL"
            demo_tag = (
                " · DEMO"
                if "DEMO" in (link.get("name") or "").upper()
                or "DEMO" in (link.get("description") or "").upper()
                else ""
            )
            st.markdown(
                f"**{link['name']}** "
                f'<span class="mccc-badge">{badge}{demo_tag}</span>',
                unsafe_allow_html=True,
            )
            if link.get("description"):
                st.write(link["description"])
            if link.get("features"):
                st.caption(f"Features: {link['features']}")
            if link.get("networks"):
                st.caption(f"Networks: {link['networks']}")
            st.markdown(
                f"**Official website (verify):** [{link['official_url']}]({link['official_url']})"
            )
            if (link.get("referral_url") or "").strip():
                st.caption(
                    "A separate referral URL may be used for Track & open — "
                    "always compare against the official website above."
                )
            partner_cta(link, key_prefix="wallet_dir", source_page="wallet_directory")
            st.divider()

st.caption("Listings are for research convenience — not endorsements of safety or profitability.")

footer("Wallet Hub")
