"""Crypto Directory — full partner ecosystem listings by category (central DB only)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import init_db
from mccc.partners import CATEGORIES, list_partner_links, section_title
from mccc.ui import (
    affiliate_disclosure,
    empty_state,
    footer,
    hero,
    page_setup,
    partner_cta,
    referral_leave_disclosure,
    section_header,
    seed_phrase_warning,
)

page_setup("crypto_directory", "Crypto Directory")
hero(
    "Crypto Directory",
    "Wallets · CEX · DEX · Explorers · Tools · Education — one catalog, central partner-link routing.",
    show_demo_banner=True,
)

init_db()
affiliate_disclosure()
referral_leave_disclosure()
seed_phrase_warning()

st.caption(
    "Action buttons resolve through `partners.resolve_outbound` — never hardcoded referral URLs. "
    "Referral placement is not a safety or performance claim."
)

hubs = st.columns(4)
with hubs[0]:
    st.page_link("pages/19_Wallet_Directory.py", label="Wallet Hub", icon="👛")
with hubs[1]:
    st.page_link("pages/20_Exchange_Directory.py", label="Exchange Hub", icon="🏦")
with hubs[2]:
    st.page_link("pages/34_DEX_Hub.py", label="DEX Hub", icon="🔄")
with hubs[3]:
    st.page_link("pages/32_Chain_Explorers.py", label="Explorers", icon="🔗")

filter_cat = st.selectbox("Category filter", ["(all)", *CATEGORIES])
status_note = st.caption("Public view: Active listings only.")

active = list_partner_links(status="Active")
if filter_cat != "(all)":
    active = [L for L in active if L.get("category") == filter_cat]

by_cat: dict[str, list] = {c: [] for c in CATEGORIES}
for link in active:
    by_cat.setdefault(link["category"], []).append(link)

cats = CATEGORIES if filter_cat == "(all)" else (filter_cat,)
for cat in cats:
    section_header(section_title(cat), f"Active {cat} listings")
    links = by_cat.get(cat, [])
    if not links:
        empty_state(f"No active {cat} listings", "Add via Admin → Partner Links.")
        continue
    for link in links:
        with st.container():
            badge = "REFERRAL" if link.get("is_referral") else "OFFICIAL"
            demo_tag = (
                " · DEMO"
                if "DEMO" in (link.get("name") or "").upper()
                or "DEMO" in (link.get("description") or "").upper()
                else ""
            )
            logo = link.get("logo_url") or ""
            cols = st.columns((0.15, 0.85)) if logo else st.columns((0.01, 0.99))
            with cols[0]:
                if logo:
                    try:
                        st.image(logo, width=56)
                    except Exception:
                        st.caption("logo")
            with cols[1]:
                st.markdown(
                    f"**{link['name']}** · `{link['category']}` "
                    f'<span class="mccc-badge">{badge}{demo_tag}</span>',
                    unsafe_allow_html=True,
                )
                if link.get("description"):
                    st.write(link["description"])
                bits = []
                if link.get("networks"):
                    bits.append(f"Networks: {link['networks']}")
                if link.get("features"):
                    bits.append(f"Features: {link['features']}")
                if bits:
                    st.caption(" · ".join(bits))
                st.markdown(
                    f"**Official URL (verify):** [{link['official_url']}]({link['official_url']})"
                )
                partner_cta(link, key_prefix="crypto_dir", source_page="crypto_directory")
            st.divider()

footer("Crypto Directory")
