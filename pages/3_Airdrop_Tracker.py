"""Stage 3 — Airdrop Tracker."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.db import add_airdrop, delete_airdrop, init_db, list_airdrops, update_airdrop
from mccc.ui import demo_callout, hero, page_setup

page_setup("airdrop_tracker", "Airdrop Tracker")
hero("Airdrop Tracker", "Track campaigns, eligibility notes, and status. Seed rows are DEMO examples.")
demo_callout("DEMO seed airdrops are examples for research practice — not live eligibility claims.")

init_db()
STATUSES = ["watching", "eligible", "in_progress", "claimed", "missed", "scam_risk"]

with st.form("add_airdrop", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Project name")
    chain = c2.text_input("Chain")
    status = c3.selectbox("Status", STATUSES)
    notes = st.text_area("Eligibility notes")
    c4, c5 = st.columns(2)
    value = c4.text_input("Estimated value", value="DEMO / unknown")
    deadline = c5.text_input("Deadline", placeholder="YYYY-MM-DD or TBD")
    if st.form_submit_button("Add airdrop", type="primary"):
        if name.strip():
            add_airdrop(name, chain, status, notes, value, deadline)
            st.success("Airdrop saved.")
            st.rerun()
        else:
            st.error("Project name required.")

rows = list_airdrops()
st.subheader(f"Tracked airdrops ({len(rows)})")
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if rows:
    ids = {f"#{r['id']} — {r['project_name']}": r["id"] for r in rows}
    pick = st.selectbox("Edit entry", list(ids.keys()))
    aid = ids[pick]
    cur = next(r for r in rows if r["id"] == aid)
    with st.form("edit_airdrop"):
        name = st.text_input("Project name", value=cur["project_name"])
        chain = st.text_input("Chain", value=cur["chain"] or "")
        status = st.selectbox("Status", STATUSES, index=STATUSES.index(cur["status"]) if cur["status"] in STATUSES else 0)
        notes = st.text_area("Eligibility notes", value=cur["eligibility_notes"] or "")
        value = st.text_input("Estimated value", value=cur["estimated_value"] or "DEMO / unknown")
        deadline = st.text_input("Deadline", value=cur["deadline"] or "")
        a, b = st.columns(2)
        if a.form_submit_button("Save", type="primary"):
            update_airdrop(aid, project_name=name, chain=chain, status=status, eligibility_notes=notes, estimated_value=value, deadline=deadline)
            st.success("Updated.")
            st.rerun()
        if b.form_submit_button("Delete"):
            delete_airdrop(aid)
            st.warning("Deleted.")
            st.rerun()
