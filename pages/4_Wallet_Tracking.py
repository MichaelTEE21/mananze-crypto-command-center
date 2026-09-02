"""Wallet tracking (public addresses only) — stronger security gate."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.db import add_wallet, delete_wallet, init_db, list_wallets, log_event
from mccc.demo_data import DEMO_WALLET_BALANCES
from mccc.partners import list_partner_links
from mccc.subscriptions import check_limit, require_can_add
from mccc.ui import (
    affiliate_disclosure,
    demo_callout,
    empty_state,
    footer,
    hero,
    page_setup,
    partner_cta,
    seed_phrase_warning,
    session_user_id,
    upgrade_cta,
)
from mccc.wallets import balance_rows_for_address, validate_public_address
from mccc.watchlist import add_item as add_watch_item

page_setup("wallet_tracking", "Wallet Tracking")
hero(
    "ANALYZE A PUBLIC WALLET",
    "PASTE A WALLET. SEE THE STORY BEHIND THE ADDRESS. · Public addresses only",
)
st.caption(
    "Public trail: transactions, token movements, protocol interactions, activity over time (when providers respond). "
    "MCCC does not need control of your wallet to analyse public blockchain activity. "
    "Helps answer: What is this wallet actually doing on-chain? — not what to buy/sell."
)
st.page_link("pages/24_Intelligence_Center.py", label="Open Intelligence Report · ANALYSE →", icon="🛰️")


init_db()

st.error(
    "PUBLIC ADDRESS ONLY — SECURITY: MCCC will never ask for seed phrases, private keys, "
    "wallet passwords, or recovery phrases. Only paste public addresses. "
    "Anything resembling a secret is rejected and not stored."
)
st.warning(
    "Do **not** paste: BIP39 recovery phrases, hex private keys, wallet/exchange passwords, "
    "or 2FA authenticator secrets — into address, label, or notes fields."
)
seed_phrase_warning()
demo_callout("Balances may be DEMO or from public RPCs/explorers — source is labelled per row.")

st.page_link(
    "pages/19_Wallet_Directory.py",
    label="→ Wallet Directory (learn before you connect)",
)
st.page_link("pages/8_Education.py", label="→ Education · key safety lessons")

if "wallet_beginner_ok" not in st.session_state:
    st.session_state["wallet_beginner_ok"] = False

if not st.session_state["wallet_beginner_ok"]:
    st.warning("Beginner gate — confirm you understand public vs private keys.")
    st.markdown(
        """
        - **Public address** = shareable receive address (safe to watch).
        - **Private key / seed** = spending authority — **never** enter here.
        - DEMO addresses are for practice only.
        - Prefer the Wallet Directory + Education lessons before connecting software wallets.
        """
    )
    if st.checkbox("I will only enter public addresses (never seeds or private keys)"):
        if st.button("Continue to wallet tracking", type="primary"):
            st.session_state["wallet_beginner_ok"] = True
            st.rerun()
    st.stop()

with st.expander("Approved wallets (Partner Directory)", expanded=False):
    affiliate_disclosure()
    wallets_partners = list_partner_links(status="Active", category="Wallet")
    if not wallets_partners:
        st.caption("No Active Wallet partners in the central directory yet.")
    else:
        for link in wallets_partners:
            st.markdown(f"**{link['name']}** — {link.get('description') or ''}")
            if link.get("official_url"):
                st.caption(f"Official: {link['official_url']}")
            partner_cta(link, key_prefix="wallet_approved", source_page="wallet_tracking")
            st.divider()

_uid = session_user_id()
_w_gate = check_limit("wallets", user_id=_uid)
if _w_gate.get("upgrade_cta"):
    st.warning(_w_gate["message"])
    upgrade_cta(_w_gate["message"])
elif not _w_gate.get("unlimited"):
    st.caption(_w_gate["message"])

CHAINS = ["ethereum", "arbitrum", "base", "optimism", "polygon", "solana", "other"]

with st.expander("Add DEMO watch addresses (one click)", expanded=False):
    if st.button("Seed two DEMO addresses"):
        try:
            require_can_add("wallets", user_id=_uid)
        except ValueError as e:
            st.error(str(e))
            upgrade_cta(str(e))
            st.stop()
        for addr, meta in DEMO_WALLET_BALANCES.items():
            existing = {w["address"] for w in list_wallets()}
            if addr not in existing:
                gate = check_limit("wallets", user_id=_uid)
                if not gate["allowed"]:
                    st.warning(gate["message"])
                    break
                add_wallet(meta["label"], addr, meta["chain"], "DEMO seed watch address")
        st.success("DEMO addresses added.")
        st.rerun()

with st.form("add_wallet", clear_on_submit=True):
    c1, c2 = st.columns(2)
    label = c1.text_input("Label", placeholder="Research watch #1")
    chain = c2.selectbox("Chain", CHAINS)
    address = st.text_input("Public address", placeholder="0x… or 0xDEMO…")
    notes = st.text_input("Notes (optional — no secrets)")
    also_watch = st.checkbox("Also add to Watchlist (type=wallet)", value=False)
    if st.form_submit_button("Add watch address", type="primary"):
        try:
            require_can_add("wallets", user_id=_uid)
            addr = validate_public_address(address, chain)
            if not label.strip():
                raise ValueError("Label required")
            add_wallet(label, addr, chain, notes)
            if also_watch:
                add_watch_item(addr, item_type="wallet", notes=label)
            log_event("wallet_added", page_key="wallet_tracking", meta=addr[:12])
            st.success("Watch address saved (public only).")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

wallets = list_wallets()
st.subheader(f"Watchlist ({len(wallets)})")
if not wallets:
    empty_state("No addresses yet", "Add a public address or seed DEMO watches.")
else:
    st.dataframe(pd.DataFrame(wallets), use_container_width=True, hide_index=True)

    pick_map = {f"#{w['id']} {w['label']} ({w['address'][:10]}…)": w for w in wallets}
    pick = st.selectbox("Inspect balances", list(pick_map.keys()))
    w = pick_map[pick]
    rows = balance_rows_for_address(w["address"], w["chain"])
    st.markdown(f"**Balances for `{w['address']}`**")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if st.button("Remove from watchlist"):
        delete_wallet(w["id"])
        st.warning("Removed.")
        st.rerun()

footer("Wallet Tracking")
