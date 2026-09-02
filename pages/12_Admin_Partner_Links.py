"""Stage 12 — Admin: partner links CRUD + click analytics (local password gate)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.db import init_db
from mccc.partners import (
    CATEGORIES,
    STATUSES,
    add_partner_link,
    click_analytics,
    delete_partner_link,
    get_partner_link,
    list_partner_links,
    set_partner_status,
    update_partner_link,
)
from mccc.ui import affiliate_disclosure, hero, page_setup, seed_phrase_warning

DEMO_ADMIN_PASSWORD = "mccc-admin-demo"


def _admin_password() -> str:
    return os.environ.get("MCCC_ADMIN_PASSWORD") or DEMO_ADMIN_PASSWORD


def _is_unlocked() -> bool:
    return bool(st.session_state.get("mccc_admin_unlocked"))


page_setup("admin_partner_links", "Admin Partner Links")
hero(
    "Admin → Partner Links",
    "Central CRUD for partner / referral URLs. Never store seed phrases or private keys here.",
)

init_db()
seed_phrase_warning()
affiliate_disclosure()

if not os.environ.get("MCCC_ADMIN_PASSWORD"):
    st.warning(
        "Using **local DEMO** admin password `mccc-admin-demo` "
        "(set `MCCC_ADMIN_PASSWORD` in `.env` for your own gate). Demo only — not production auth."
    )

if not _is_unlocked():
    with st.form("admin_unlock"):
        pw = st.text_input("Admin password", type="password")
        if st.form_submit_button("Unlock", type="primary"):
            if pw == _admin_password():
                st.session_state["mccc_admin_unlocked"] = True
                st.success("Unlocked for this session.")
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

if st.sidebar.button("Lock admin"):
    st.session_state["mccc_admin_unlocked"] = False
    st.rerun()

st.success("Admin unlocked (session).")

# --- Analytics ---
st.subheader("Click analytics (aggregated only)")
analytics = click_analytics()
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total clicks", analytics["total_clicks"])
per_cat = analytics["per_category"]
m2.metric("Wallet", per_cat.get("Wallet", 0))
m3.metric("CEX", per_cat.get("CEX", 0))
m4.metric("DEX", per_cat.get("DEX", 0))
m5.metric("Tool", per_cat.get("Crypto Tool", 0))
m6.metric("Partner", per_cat.get("Partner", 0))

plat_df = pd.DataFrame(analytics["per_platform"])
if not plat_df.empty:
    st.dataframe(
        plat_df.rename(columns={"id": "ID", "name": "Platform", "category": "Category", "clicks": "Clicks"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("No platforms yet.")

st.divider()

# --- Create / Edit form ---
st.subheader("Add or edit partner link")
all_links = list_partner_links()
edit_options = {"— New link —": None}
for L in all_links:
    edit_options[f"#{L['id']} {L['name']} ({L['status']})"] = L["id"]

pick = st.selectbox("Edit existing", list(edit_options.keys()))
edit_id = edit_options[pick]
existing = get_partner_link(edit_id) if edit_id else None

with st.form("partner_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    name = c1.text_input("Name", value=(existing or {}).get("name", ""))
    category = c2.selectbox(
        "Category",
        list(CATEGORIES),
        index=list(CATEGORIES).index(existing["category"]) if existing and existing["category"] in CATEGORIES else 0,
    )
    official_url = st.text_input("Official website", value=(existing or {}).get("official_url", ""))
    referral_url = st.text_input(
        "Referral / partner link (optional — empty = use official)",
        value=(existing or {}).get("referral_url", ""),
    )
    description = st.text_area("Description", value=(existing or {}).get("description", ""))
    features = st.text_input("Features (short / comma)", value=(existing or {}).get("features", ""))
    networks = st.text_input("Networks / platforms", value=(existing or {}).get("networks", ""))
    logo_url = st.text_input("Logo URL (optional)", value=(existing or {}).get("logo_url", ""))
    status = st.selectbox(
        "Status",
        list(STATUSES),
        index=list(STATUSES).index(existing["status"]) if existing and existing["status"] in STATUSES else 0,
    )
    submitted = st.form_submit_button("Save", type="primary")
    if submitted:
        if not name.strip() or not official_url.strip():
            st.error("Name and official website are required.")
        else:
            try:
                if edit_id:
                    update_partner_link(
                        edit_id,
                        name=name,
                        category=category,
                        official_url=official_url,
                        referral_url=referral_url,
                        description=description,
                        features=features,
                        networks=networks,
                        logo_url=logo_url,
                        status=status,
                    )
                    st.success(f"Updated #{edit_id}.")
                else:
                    nid = add_partner_link(
                        name=name,
                        category=category,
                        official_url=official_url,
                        referral_url=referral_url,
                        description=description,
                        features=features,
                        networks=networks,
                        logo_url=logo_url,
                        status=status,
                    )
                    st.success(f"Created #{nid}.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()
st.subheader("Existing links")
links = list_partner_links()
if not links:
    st.write("No partner links yet.")
else:
    st.dataframe(
        pd.DataFrame(links)[
            [
                "id",
                "name",
                "category",
                "official_url",
                "referral_url",
                "status",
                "is_referral",
                "updated_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    action_map = {f"#{L['id']} {L['name']}": L for L in links}
    target = st.selectbox("Select for Enable / Disable / Delete", list(action_map.keys()))
    row = action_map[target]
    a, b, c = st.columns(3)
    with a:
        if st.button("Enable", use_container_width=True):
            set_partner_status(row["id"], "Active")
            st.rerun()
    with b:
        if st.button("Disable", use_container_width=True):
            set_partner_status(row["id"], "Disabled")
            st.rerun()
    with c:
        if st.button("Delete permanently", use_container_width=True):
            delete_partner_link(row["id"])
            st.warning("Deleted.")
            st.rerun()
