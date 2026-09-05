"""Admin — Partner click analytics (privacy-conscious aggregates only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.auth import get_session_user
from mccc.db import init_db
from mccc.partners import CATEGORIES, POSTGRES_NOTE, click_analytics, partner_ecosystem_summary
from mccc.ui import affiliate_disclosure, footer, hero, page_setup, seed_phrase_warning

DEMO_ADMIN_PASSWORD = "mccc-admin-demo"


def _admin_password() -> str:
    return os.environ.get("MCCC_ADMIN_PASSWORD") or DEMO_ADMIN_PASSWORD


def _is_unlocked() -> bool:
    if st.session_state.get("mccc_admin_unlocked"):
        return True
    user = get_session_user()
    if user and user.get("is_admin"):
        return True
    return False


page_setup("admin_partner_analytics", "Partner Analytics")
hero(
    "Admin → Partner Analytics",
    "Aggregates only: platform, category, count, date. No IP, UA, or unnecessary PII.",
)

init_db()
seed_phrase_warning()
affiliate_disclosure()

if not _is_unlocked():
    st.caption("Unlock with `MCCC_ADMIN_PASSWORD` or an `is_admin` session.")
    with st.form("analytics_unlock"):
        pw = st.text_input("Admin password", type="password")
        if st.form_submit_button("Unlock", type="primary"):
            if pw == _admin_password():
                st.session_state["mccc_admin_unlocked"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

summary = partner_ecosystem_summary()
analytics = click_analytics()

c1, c2, c3 = st.columns(3)
c1.metric("Active platforms", summary["active_total"])
c2.metric("Total clicks", analytics["total_clicks"])
c3.metric("Categories tracked", len(CATEGORIES))

st.subheader("Clicks by category")
cat_df = pd.DataFrame(
    [{"category": k, "clicks": v} for k, v in analytics["per_category"].items()]
)
st.dataframe(cat_df, use_container_width=True, hide_index=True)
if not cat_df.empty and cat_df["clicks"].sum() > 0:
    st.bar_chart(cat_df.set_index("category"))

st.subheader("Clicks by platform")
plat = pd.DataFrame(analytics["per_platform"])
if not plat.empty:
    st.dataframe(
        plat.rename(columns={"id": "ID", "name": "Platform", "category": "Category", "clicks": "Clicks"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("No platforms yet.")

st.subheader("Clicks by date (UTC day)")
dates = pd.DataFrame(analytics.get("per_date") or [])
if not dates.empty:
    st.dataframe(
        dates.rename(columns={"day": "Date", "clicks": "Clicks"}),
        use_container_width=True,
        hide_index=True,
    )
    st.bar_chart(dates.set_index("day")["clicks"])
else:
    st.caption("No clicks recorded yet.")

st.subheader("Active listings by category")
by = summary.get("by_category") or {}
st.dataframe(
    pd.DataFrame([{"category": k, "active": v} for k, v in by.items()]),
    use_container_width=True,
    hide_index=True,
)

st.info(POSTGRES_NOTE)
st.page_link("pages/12_Admin_Partner_Links.py", label="Open Partner Links CRUD", icon="🔗")
footer("Partner Analytics")
