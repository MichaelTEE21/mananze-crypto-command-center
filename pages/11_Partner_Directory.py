"""Stage 11 — Partner / platform directory (Active links only)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import init_db
from mccc.partners import CATEGORIES, list_partner_links
from mccc.ui import affiliate_disclosure, hero, page_setup, partner_cta, seed_phrase_warning, footer

page_setup("partner_directory", "Partner Directory")
hero(
    "Platform Directory",
    "Wallets, exchanges, DEX, tools & partners — links from the central DB only. DEMO rows are labelled.",
    show_demo_banner=True,
)

init_db()
affiliate_disclosure()
seed_phrase_warning()

st.caption(
    "Listings are for research convenience. Referral placement does **not** mean a platform is "
    "safer, better, or more profitable."
)

SECTION_META = {
    "Wallet": ("WALLETS", "Download / Visit Wallet"),
    "CEX": ("CENTRALIZED EXCHANGES", "Join Exchange"),
    "DEX": ("DECENTRALIZED EXCHANGES", "Explore DEX"),
    "Crypto Tool": ("CRYPTO TOOLS", "Visit Platform"),
    "Partner": ("PARTNERS", "Visit Platform"),
}

active = list_partner_links(status="Active")
by_cat: dict[str, list] = {c: [] for c in CATEGORIES}
for link in active:
    by_cat.setdefault(link["category"], []).append(link)

for cat in CATEGORIES:
    title, _ = SECTION_META[cat]
    links = by_cat.get(cat, [])
    st.subheader(title)
    if not links:
        st.write("_No active listings in this section._")
        continue
    for link in links:
        with st.container():
            cols = st.columns((0.18, 0.82)) if link.get("logo_url") else st.columns((0.01, 0.99))
            with cols[0]:
                if link.get("logo_url"):
                    try:
                        st.image(link["logo_url"], width=64)
                    except Exception:
                        st.caption("logo")
            with cols[1]:
                badge = "REFERRAL" if link.get("is_referral") else "OFFICIAL"
                demo_tag = " · DEMO" if "DEMO" in (link.get("name") or "").upper() or "DEMO" in (link.get("description") or "").upper() else ""
                st.markdown(
                    f"**{link['name']}** · `{link['category']}` "
                    f'<span class="mccc-badge">{badge}{demo_tag}</span>',
                    unsafe_allow_html=True,
                )
                if link.get("description"):
                    st.write(link["description"])
                meta_bits = []
                if link.get("features"):
                    meta_bits.append(f"**Features:** {link['features']}")
                if link.get("networks"):
                    meta_bits.append(f"**Networks:** {link['networks']}")
                if meta_bits:
                    st.caption(" · ".join(meta_bits))
                st.markdown(f"**Official website (verify):** [{link['official_url']}]({link['official_url']})")
                partner_cta(link, key_prefix="dir", source_page="partner_directory")
        st.divider()

footer("Partner Directory")
