"""Airdrop Tracker — richer fields, filters, tasks."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.airdrop_tasks import add_task, delete_task, list_tasks, toggle_done
from mccc.db import (
    AIRDROP_STATUSES,
    add_airdrop,
    delete_airdrop,
    init_db,
    list_airdrops,
    update_airdrop,
)
from mccc.ui import demo_callout, empty_state, hero, page_setup

page_setup("airdrop_tracker", "Airdrop Tracker")
hero("Airdrop Tracker", "Campaigns, eligibility notes, statuses, and task checklists.")
demo_callout("DEMO seed airdrops are examples for research practice — not live eligibility claims.")

init_db()

with st.expander("Add airdrop", expanded=False):
    with st.form("add_airdrop", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Project name")
        chain = c2.text_input("Chain")
        status = c3.selectbox("Status", list(AIRDROP_STATUSES))
        notes = st.text_area("Eligibility notes")
        c4, c5, c6 = st.columns(3)
        value = c4.text_input("Estimated value", value="DEMO / unknown")
        deadline = c5.text_input("Deadline", placeholder="YYYY-MM-DD or TBD")
        token = c6.text_input("Token")
        c7, c8, c9 = st.columns(3)
        points = c7.text_input("Points")
        claim_page = c8.text_input("Claim page URL")
        official = c9.text_input("Official website")
        if st.form_submit_button("Add airdrop", type="primary"):
            if name.strip():
                add_airdrop(
                    name,
                    chain,
                    status,
                    notes,
                    value,
                    deadline,
                    token=token,
                    points=points,
                    claim_page=claim_page,
                    official_website=official,
                )
                st.success("Airdrop saved.")
                st.rerun()
            else:
                st.error("Project name required.")

rows = list_airdrops()
fc1, fc2, fc3 = st.columns(3)
q = fc1.text_input("Search", placeholder="name / chain / token").strip().lower()
status_f = fc2.selectbox("Filter status", ["(all)"] + list(AIRDROP_STATUSES))
chain_f = fc3.text_input("Filter chain").strip().lower()

filtered = []
for r in rows:
    blob = " ".join(str(v) for v in r.values()).lower()
    if q and q not in blob:
        continue
    if status_f != "(all)" and r.get("status") != status_f:
        continue
    if chain_f and chain_f not in (r.get("chain") or "").lower():
        continue
    filtered.append(r)

st.subheader(f"Tracked airdrops ({len(filtered)} / {len(rows)})")
if not filtered:
    empty_state("No matching airdrops", "Adjust filters or add a campaign.")
else:
    cols_show = [
        "id",
        "project_name",
        "chain",
        "status",
        "token",
        "points",
        "estimated_value",
        "deadline",
        "claim_page",
        "official_website",
    ]
    view = [{k: r.get(k) for k in cols_show} for r in filtered]
    st.dataframe(pd.DataFrame(view), use_container_width=True, hide_index=True)

if filtered:
    ids = {f"#{r['id']} — {r['project_name']}": r["id"] for r in filtered}
    pick = st.selectbox("Edit entry", list(ids.keys()))
    aid = ids[pick]
    cur = next(r for r in rows if r["id"] == aid)

    with st.form("edit_airdrop"):
        name = st.text_input("Project name", value=cur["project_name"])
        chain = st.text_input("Chain", value=cur["chain"] or "")
        status = st.selectbox(
            "Status",
            list(AIRDROP_STATUSES),
            index=list(AIRDROP_STATUSES).index(cur["status"])
            if cur.get("status") in AIRDROP_STATUSES
            else 0,
        )
        notes = st.text_area("Eligibility notes", value=cur["eligibility_notes"] or "")
        value = st.text_input("Estimated value", value=cur["estimated_value"] or "DEMO / unknown")
        deadline = st.text_input("Deadline", value=cur["deadline"] or "")
        token = st.text_input("Token", value=cur.get("token") or "")
        points = st.text_input("Points", value=cur.get("points") or "")
        claim_page = st.text_input("Claim page", value=cur.get("claim_page") or "")
        official = st.text_input("Official website", value=cur.get("official_website") or "")
        a, b = st.columns(2)
        if a.form_submit_button("Save", type="primary"):
            update_airdrop(
                aid,
                project_name=name,
                chain=chain,
                status=status,
                eligibility_notes=notes,
                estimated_value=value,
                deadline=deadline,
                token=token,
                points=points,
                claim_page=claim_page,
                official_website=official,
            )
            st.success("Updated.")
            st.rerun()
        if b.form_submit_button("Delete"):
            delete_airdrop(aid)
            st.warning("Deleted.")
            st.rerun()

    st.subheader("Task checklist")
    tasks = list_tasks(aid)
    with st.form("add_task", clear_on_submit=True):
        ttitle = st.text_input("New task")
        if st.form_submit_button("Add task"):
            if ttitle.strip():
                add_task(aid, ttitle.strip())
                st.rerun()
    if not tasks:
        empty_state("No tasks", "Break eligibility work into checklist items.")
    else:
        for t in tasks:
            cols = st.columns((0.15, 0.7, 0.15))
            done = cols[0].checkbox("Done", value=bool(t["done"]), key=f"task_{t['id']}", label_visibility="collapsed")
            if done != bool(t["done"]):
                toggle_done(t["id"], done=done)
                st.rerun()
            cols[1].write(t["title"])
            if cols[2].button("✕", key=f"tdel_{t['id']}"):
                delete_task(t["id"])
                st.rerun()
