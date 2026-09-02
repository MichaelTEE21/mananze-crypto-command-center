"""Project Tracker — kanban by stage + detail expander."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.db import (
    PROJECT_STAGES,
    add_project,
    delete_project,
    init_db,
    list_projects,
    log_event,
    update_project,
)
from mccc.ui import empty_state, hero, page_setup

page_setup("project_tracker", "Project Tracker")
hero("Project Tracker", "Research pipeline by stage — SQLite local store.")

init_db()

with st.expander("Add project", expanded=True):
    with st.form("add_project", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name", placeholder="e.g. DEMO: Bridge risk map")
        chain = c2.text_input("Chain", placeholder="ethereum / solana / multi")
        stage = c3.selectbox("Stage", list(PROJECT_STAGES), index=1)
        notes = st.text_area("Notes", placeholder="Sources, open questions…")
        c4, c5, c6 = st.columns(3)
        priority = c4.slider("Priority (1=highest)", 1, 5, 3)
        risk = c5.text_input("Risk rating", placeholder="med")
        category = c6.text_input("Category", placeholder="L2 / DeFi…")
        c7, c8 = st.columns(2)
        website = c7.text_input("Website")
        docs = c8.text_input("Docs URL")
        next_action = st.text_input("Next action")
        if st.form_submit_button("Add project", type="primary"):
            if name.strip():
                add_project(
                    name,
                    chain,
                    status=stage.lower(),
                    notes=notes,
                    priority=priority,
                    stage=stage,
                    risk_rating=risk,
                    category=category,
                    website=website,
                    docs=docs,
                    next_action=next_action,
                )
                log_event("case_opened", page_key="project_tracker", meta=name.strip()[:80])
                st.success("Project saved.")
                st.rerun()
            else:
                st.error("Name is required.")

projects = list_projects()
st.subheader(f"Pipeline ({len(projects)})")
if not projects:
    empty_state("No projects yet", "Add one above. Seed DEMO rows appear on first launch.")
else:
    cols = st.columns(len(PROJECT_STAGES))
    by_stage: dict[str, list] = {s: [] for s in PROJECT_STAGES}
    for p in projects:
        stage = p.get("stage") or "Researching"
        if stage not in by_stage:
            by_stage.setdefault(stage, [])
        by_stage[stage].append(p)
    for i, stage in enumerate(PROJECT_STAGES):
        with cols[i]:
            st.markdown(f"**{stage}** · {len(by_stage.get(stage, []))}")
            for p in by_stage.get(stage, [])[:12]:
                st.markdown(
                    f'<div class="mccc-kanban"><div class="title">#{p["id"]} {p["name"]}</div>'
                    f'<div class="meta">{p.get("chain") or "—"} · P{p.get("priority")}</div></div>',
                    unsafe_allow_html=True,
                )

    st.subheader("Table")
    st.dataframe(pd.DataFrame(projects), use_container_width=True, hide_index=True)

    st.subheader("Detail / edit")
    ids = {f"#{p['id']} — {p['name']}": p["id"] for p in projects}
    pick = st.selectbox("Select project", list(ids.keys()))
    pid = ids[pick]
    current = next(p for p in projects if p["id"] == pid)
    with st.expander("Full detail", expanded=True):
        st.json({k: current.get(k) for k in current if k not in ()})
    with st.form("edit_project"):
        name = st.text_input("Name", value=current["name"])
        chain = st.text_input("Chain", value=current["chain"] or "")
        stage_idx = (
            list(PROJECT_STAGES).index(current["stage"])
            if current.get("stage") in PROJECT_STAGES
            else 1
        )
        stage = st.selectbox("Stage", list(PROJECT_STAGES), index=stage_idx)
        notes = st.text_area("Notes", value=current["notes"] or "")
        priority = st.slider("Priority", 1, 5, int(current["priority"] or 3))
        risk = st.text_input("Risk rating", value=current.get("risk_rating") or "")
        category = st.text_input("Category", value=current.get("category") or "")
        website = st.text_input("Website", value=current.get("website") or "")
        docs = st.text_input("Docs", value=current.get("docs") or "")
        next_action = st.text_input("Next action", value=current.get("next_action") or "")
        last_checked = st.text_input("Last checked", value=current.get("last_checked") or "")
        token = st.text_input("Token", value=current.get("token") or "")
        col_a, col_b = st.columns(2)
        save = col_a.form_submit_button("Save changes", type="primary")
        delete = col_b.form_submit_button("Delete")
        if save:
            update_project(
                pid,
                name=name,
                chain=chain,
                status=stage.lower(),
                stage=stage,
                notes=notes,
                priority=priority,
                risk_rating=risk,
                category=category,
                website=website,
                docs=docs,
                next_action=next_action,
                last_checked=last_checked,
                token=token,
            )
            st.success("Updated.")
            st.rerun()
        if delete:
            delete_project(pid)
            st.warning("Deleted.")
            st.rerun()
