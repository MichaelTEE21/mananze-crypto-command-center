"""DEX Hub — decentralized exchange partner listings + never-ask-keys banner."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import init_db
from mccc.exchanges import list_exchanges, resolve_visit_url as resolve_exchange_url
from mccc.partners import list_partner_links
from mccc.ui import (
    affiliate_disclosure,
    demo_callout,
    empty_state,
    footer,
    hero,
    page_setup,
    partner_cta,
    referral_leave_disclosure,
    section_header,
    seed_phrase_warning,
)

page_setup("dex_hub", "DEX Hub")
hero(
    "DEX Hub",
    "Decentralized exchange research listings from central Partner Links (+ optional exchanges table).",
    show_demo_banner=True,
)

init_db()
affiliate_disclosure()
referral_leave_disclosure()
seed_phrase_warning()

st.error(
    "SECURITY: MCCC never asks for seed phrases, private keys, wallet passwords, or 2FA secrets. "
    "Connecting a wallet on an external DEX is your responsibility — verify URLs character-by-character."
)
demo_callout("DEMO partner rows use example.com — not live venues. No profit or safety guarantees.")

section_header("Partner Directory — DEX", "Active DEX category from partner_links")
dex_partners = list_partner_links(status="Active", category="DEX")
if not dex_partners:
    empty_state("No Active DEX partners yet", "Admin → Partner Links can add DEX category rows.")
else:
    for link in dex_partners:
        badge = "REFERRAL" if (link.get("referral_url") or "").strip() else "OFFICIAL"
        demo_tag = (
            " · DEMO"
            if "DEMO" in (link.get("name") or "").upper()
            or "DEMO" in (link.get("description") or "").upper()
            else ""
        )
        st.markdown(
            f"**{link['name']}** <span class=\"mccc-badge\">{badge}{demo_tag}</span>",
            unsafe_allow_html=True,
        )
        if link.get("description"):
            st.write(link["description"])
        if link.get("networks"):
            st.caption(f"Networks: {link['networks']}")
        st.markdown(f"**Official (verify):** [{link['official_url']}]({link['official_url']})")
        partner_cta(link, key_prefix="dex_hub", source_page="dex_hub")
        st.divider()

section_header("Exchanges table — DEX type", "Optional research rows (official vs referral kept separate)")
dex_ex = [r for r in list_exchanges(status="Active", type_="DEX")]
if not dex_ex:
    st.caption("No Active DEX rows in exchanges table.")
else:
    for r in dex_ex:
        url = resolve_exchange_url(r)
        st.markdown(f"**{r['name']}** · exchanges table")
        if r.get("description"):
            st.write(r["description"])
        st.caption(f"Official: {r.get('official_url') or '—'} · Outbound resolves to: `{url}`")
        if url:
            st.link_button("Visit (resolved)", url, use_container_width=False)

st.page_link("pages/33_Crypto_Directory.py", label="Back to Crypto Directory", icon="🗂️")
footer("DEX Hub")
