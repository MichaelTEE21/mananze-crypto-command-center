"""Stage 2 — Project Tracker with SQLite persistence."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.db import add_project, delete_project, init_db, list_projects, log_event, update_project
from mccc.ui import hero, page_setup

page_setup("project_tracker", "Project Tracker")
hero("Project Tracker", "Capture crypto research projects, status, and notes — SQLite local store.")

init_db()
STATUSES = ["researching", "watching", "diligence", "archived", "pass"]

st.subheader("Add project")
with st.form("add_project", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name", placeholder="e.g. DEMO: Bridge risk map")
    chain = c2.text_input("Chain", placeholder="ethereum / solana / multi")
    status = c3.selectbox("Status", STATUSES)
    notes = st.text_area("Notes", placeholder="Sources, open questions…")
    priority = st.slider("Priority (1=highest)", 1, 5, 3)
    if st.form_submit_button("Add project", type="primary"):
        if name.strip():
            add_project(name, chain, status, notes, priority)
            log_event("case_opened", page_key="project_tracker", meta=name.strip()[:80])
            st.success("Project saved.")
            st.rerun()
        else:
            st.error("Name is required.")

projects = list_projects()
st.subheader(f"Projects ({len(projects)})")
if not projects:
    st.info("No projects yet — add one above. Seed DEMO rows appear on first launch.")
else:
    st.dataframe(pd.DataFrame(projects), use_container_width=True, hide_index=True)

    st.subheader("Edit / delete")
    ids = {f"#{p['id']} — {p['name']}": p["id"] for p in projects}
    pick = st.selectbox("Select project", list(ids.keys()))
    pid = ids[pick]
    current = next(p for p in projects if p["id"] == pid)
    with st.form("edit_project"):
        name = st.text_input("Name", value=current["name"])
        chain = st.text_input("Chain", value=current["chain"] or "")
        status = st.selectbox("Status", STATUSES, index=STATUSES.index(current["status"]) if current["status"] in STATUSES else 0)
        notes = st.text_area("Notes", value=current["notes"] or "")
        priority = st.slider("Priority", 1, 5, int(current["priority"] or 3))
        col_a, col_b = st.columns(2)
        save = col_a.form_submit_button("Save changes", type="primary")
        delete = col_b.form_submit_button("Delete")
        if save:
            update_project(pid, name=name, chain=chain, status=status, notes=notes, priority=priority)
            st.success("Updated.")
            st.rerun()
        if delete:
            delete_project(pid)
            st.warning("Deleted.")
            st.rerun()
