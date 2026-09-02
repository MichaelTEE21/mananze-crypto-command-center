"""Project Tracker — kanban by stage, rich edit, research timeline, favourites."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.bookmarks import favourite_refs, toggle_favourite
from mccc.db import (
    PROJECT_STAGES,
    add_project,
    delete_project,
    init_db,
    list_projects,
    log_event,
    normalize_project_stage,
    update_project,
)
from mccc.research import (
    EVENT_TYPES,
    add_research_event,
    delete_research_event,
    list_project_tags,
    list_research_events,
    set_project_tags,
)
from mccc.security import SensitiveCredentialError, reject_sensitive_credential
from mccc.subscriptions import check_limit, require_can_add
from mccc.ui import empty_state, footer, hero, page_setup, section_header, status_badge, session_user_id, upgrade_cta

page_setup("project_tracker", "Project Tracker")
hero("Project Tracker", "Research pipeline by stage — SQLite local store. Never paste seeds or keys into notes.")

init_db()
_uid = session_user_id()
_proj_gate = check_limit("projects", user_id=_uid)
if _proj_gate.get("upgrade_cta"):
    st.warning(_proj_gate["message"])
    upgrade_cta(_proj_gate["message"])
elif not _proj_gate.get("unlimited"):
    st.caption(_proj_gate["message"])

STAGE_KIND = {
    "DISCOVERED": "info",
    "RESEARCHING": "info",
    "FARMING": "warn",
    "WATCHLIST": "info",
    "WAITING FOR TGE": "warn",
    "COMPLETED": "success",
    "ARCHIVED": "danger",
}


def _safe_notes(text: str, field: str) -> str:
    return reject_sensitive_credential(text or "", field=field)


with st.expander("Add project", expanded=False):
    with st.form("add_project", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        name = c1.text_input("Name", placeholder="e.g. DEMO: Bridge risk map")
        ticker = c2.text_input("Ticker", placeholder="DEMO")
        chain = c3.text_input("Chain", placeholder="ethereum / solana / multi")
        stage = c4.selectbox("Stage", list(PROJECT_STAGES), index=1)
        description = st.text_area("Description", placeholder="What is this project?")
        c5, c6, c7 = st.columns(3)
        category = c5.text_input("Category", placeholder="L2 / DeFi / Infra / RWA…")
        priority = c6.slider("Priority (1=highest)", 1, 5, 3)
        personal_rating = c7.slider("Personal rating (0–5)", 0, 5, 0)
        c8, c9, c10 = st.columns(3)
        website = c8.text_input("Website")
        docs = c9.text_input("Docs URL")
        blog = c10.text_input("Blog")
        c11, c12, c13, c14 = st.columns(4)
        twitter = c11.text_input("Twitter / X")
        discord = c12.text_input("Discord")
        telegram = c13.text_input("Telegram")
        github = c14.text_input("GitHub")
        c15, c16, c17 = st.columns(3)
        funding = c15.text_input("Funding")
        investors = c16.text_input("Investors")
        token = c17.text_input("Token")
        c18, c19, c20 = st.columns(3)
        tge = c18.text_input("TGE / launch date", placeholder="YYYY-MM-DD or TBD")
        launch_status = c19.text_input("Launch status", placeholder="pre-launch / live")
        token_status = c20.text_input("Token status", placeholder="no token / TGE pending")
        research_notes = st.text_area("Research notes")
        risk_notes = st.text_area("Risk notes")
        tags = st.text_input("Tags (comma-separated)")
        next_action = st.text_input("Next action")
        if st.form_submit_button("Add project", type="primary"):
            if not name.strip():
                st.error("Name is required.")
            else:
                try:
                    require_can_add("projects", user_id=_uid)
                    _safe_notes(research_notes, "project.research_notes")
                    _safe_notes(risk_notes, "project.risk_notes")
                    _safe_notes(description, "project.description")
                    pid = add_project(
                        name,
                        chain,
                        status=stage.lower(),
                        notes=research_notes,
                        priority=priority,
                        stage=stage,
                        description=description,
                        category=category,
                        website=website,
                        docs=docs,
                        blog=blog,
                        twitter=twitter,
                        discord=discord,
                        telegram=telegram,
                        github=github,
                        funding=funding,
                        investors=investors,
                        token=token,
                        tge=tge,
                        launch_status=launch_status,
                        token_status=token_status,
                        research_notes=research_notes,
                        risk_notes=risk_notes,
                        ticker=ticker,
                        personal_rating=personal_rating,
                        tags=tags,
                        next_action=next_action,
                    )
                    if tags.strip():
                        set_project_tags(pid, tags)
                    log_event("case_opened", page_key="project_tracker", meta=name.strip()[:80])
                    st.success("Project saved.")
                    st.rerun()
                except SensitiveCredentialError as e:
                    st.error(str(e))

projects = list_projects()
fav_refs = favourite_refs("project")

# --- Filters ---
section_header("Browse", "Search · filter · sort · favourites")
fc1, fc2, fc3, fc4 = st.columns(4)
q = fc1.text_input("Search", placeholder="name / ticker / chain / tags").strip().lower()
stage_f = fc2.selectbox("Filter stage", ["(all)"] + list(PROJECT_STAGES))
chain_f = fc3.text_input("Filter chain").strip().lower()
sort_by = fc4.selectbox("Sort", ["priority", "updated_at", "name", "personal_rating", "stage"])
only_fav = st.checkbox("Favourites only", value=False)

filtered: list[dict] = []
for p in projects:
    stage_n = normalize_project_stage(p.get("stage"), p.get("status"))
    p = {**p, "stage": stage_n}
    blob = " ".join(str(v) for v in p.values() if v is not None).lower()
    if q and q not in blob:
        continue
    if stage_f != "(all)" and stage_n != stage_f:
        continue
    if chain_f and chain_f not in (p.get("chain") or "").lower():
        continue
    if only_fav and str(p["id"]) not in fav_refs:
        continue
    filtered.append(p)

reverse = sort_by in ("updated_at", "personal_rating")
filtered.sort(key=lambda r: (r.get(sort_by) is None, r.get(sort_by) or ""), reverse=reverse)

# --- Kanban ---
section_header(f"Kanban ({len(filtered)} / {len(projects)})", "Columns = product stages")
# Streamlit: 7 cols is tight — two rows
row1 = list(PROJECT_STAGES[:4])
row2 = list(PROJECT_STAGES[4:])
by_stage: dict[str, list] = {s: [] for s in PROJECT_STAGES}
for p in filtered:
    by_stage.setdefault(p["stage"], []).append(p)

for stage_row in (row1, row2):
    cols = st.columns(len(stage_row))
    for i, stage in enumerate(stage_row):
        with cols[i]:
            st.markdown(f"**{stage}** · {len(by_stage.get(stage, []))}")
            for p in by_stage.get(stage, [])[:10]:
                star = "★ " if str(p["id"]) in fav_refs else ""
                ticker = f" ({p.get('ticker')})" if p.get("ticker") else ""
                st.markdown(
                    f'<div class="mccc-kanban"><div class="title">{star}#{p["id"]} {p["name"]}{ticker}</div>'
                    f'<div class="meta">{p.get("chain") or "—"} · P{p.get("priority")} · '
                    f'★{p.get("personal_rating") or 0}</div></div>',
                    unsafe_allow_html=True,
                )

if not filtered:
    empty_state("No matching projects", "Add one above or clear filters. Seed DEMO rows appear on first launch.")
else:
    st.subheader("Table")
    cols_show = [
        "id", "name", "ticker", "stage", "chain", "category", "priority",
        "personal_rating", "token", "tge", "next_action", "tags",
    ]
    view = [{k: r.get(k) for k in cols_show} for r in filtered]
    st.dataframe(pd.DataFrame(view), use_container_width=True, hide_index=True)

    st.subheader("Detail / workspace")
    ids = {f"{'★ ' if str(p['id']) in fav_refs else ''}#{p['id']} — {p['name']}": p["id"] for p in filtered}
    pick = st.selectbox("Select project", list(ids.keys()))
    pid = ids[pick]
    current = next(p for p in projects if p["id"] == pid)
    current_stage = normalize_project_stage(current.get("stage"), current.get("status"))

    fav_col1, fav_col2 = st.columns((1, 3))
    with fav_col1:
        is_fav = str(pid) in fav_refs
        if st.button("Unfavourite ★" if is_fav else "Favourite ☆", use_container_width=True):
            toggle_favourite("project", str(pid))
            st.rerun()
    with fav_col2:
        status_badge(current_stage, STAGE_KIND.get(current_stage, "info"))

    with st.expander("Full detail (JSON)", expanded=False):
        st.json(dict(current))

    with st.form("edit_project"):
        c1, c2, c3, c4 = st.columns(4)
        name = c1.text_input("Name", value=current["name"])
        ticker = c2.text_input("Ticker", value=current.get("ticker") or "")
        chain = c3.text_input("Chain", value=current["chain"] or "")
        stage_idx = list(PROJECT_STAGES).index(current_stage) if current_stage in PROJECT_STAGES else 1
        stage = c4.selectbox("Stage", list(PROJECT_STAGES), index=stage_idx)
        description = st.text_area("Description", value=current.get("description") or "")
        c5, c6, c7 = st.columns(3)
        category = c5.text_input("Category", value=current.get("category") or "")
        priority = c6.slider("Priority", 1, 5, int(current["priority"] or 3))
        personal_rating = c7.slider("Personal rating", 0, 5, int(current.get("personal_rating") or 0))
        c8, c9, c10 = st.columns(3)
        website = c8.text_input("Website", value=current.get("website") or "")
        docs = c9.text_input("Docs", value=current.get("docs") or "")
        blog = c10.text_input("Blog", value=current.get("blog") or "")
        c11, c12, c13, c14 = st.columns(4)
        twitter = c11.text_input("Twitter / X", value=current.get("twitter") or "")
        discord = c12.text_input("Discord", value=current.get("discord") or "")
        telegram = c13.text_input("Telegram", value=current.get("telegram") or "")
        github = c14.text_input("GitHub", value=current.get("github") or "")
        c15, c16, c17 = st.columns(3)
        funding = c15.text_input("Funding", value=current.get("funding") or "")
        investors = c16.text_input("Investors", value=current.get("investors") or "")
        token = c17.text_input("Token", value=current.get("token") or "")
        c18, c19, c20 = st.columns(3)
        tge = c18.text_input("TGE", value=current.get("tge") or "")
        launch_status = c19.text_input("Launch status", value=current.get("launch_status") or "")
        token_status = c20.text_input("Token status", value=current.get("token_status") or "")
        research_notes = st.text_area(
            "Research notes",
            value=current.get("research_notes") or current.get("notes") or "",
        )
        risk_notes = st.text_area("Risk notes", value=current.get("risk_notes") or "")
        existing_tags = ", ".join(list_project_tags(pid)) or (current.get("tags") or "")
        tags = st.text_input("Tags (comma-separated)", value=existing_tags)
        next_action = st.text_input("Next action", value=current.get("next_action") or "")
        last_checked = st.text_input("Last checked", value=current.get("last_checked") or "")
        col_a, col_b = st.columns(2)
        save = col_a.form_submit_button("Save changes", type="primary")
        delete = col_b.form_submit_button("Delete")
        if save:
            try:
                _safe_notes(research_notes, "project.research_notes")
                _safe_notes(risk_notes, "project.risk_notes")
                _safe_notes(description, "project.description")
                update_project(
                    pid,
                    name=name,
                    chain=chain,
                    status=stage.lower(),
                    stage=stage,
                    notes=research_notes,
                    priority=priority,
                    description=description,
                    category=category,
                    website=website,
                    docs=docs,
                    blog=blog,
                    twitter=twitter,
                    discord=discord,
                    telegram=telegram,
                    github=github,
                    funding=funding,
                    investors=investors,
                    token=token,
                    tge=tge,
                    launch_status=launch_status,
                    token_status=token_status,
                    research_notes=research_notes,
                    risk_notes=risk_notes,
                    ticker=ticker,
                    personal_rating=personal_rating,
                    tags=tags,
                    next_action=next_action,
                    last_checked=last_checked,
                )
                set_project_tags(pid, tags)
                if current_stage != stage:
                    add_research_event(
                        pid,
                        body=f"Stage: {current_stage} → {stage}",
                        event_type="status_change",
                    )
                st.success("Updated.")
                st.rerun()
            except SensitiveCredentialError as e:
                st.error(str(e))
        if delete:
            delete_project(pid)
            st.warning("Deleted.")
            st.rerun()

    st.subheader("Research timeline")
    events = list_research_events(pid)
    with st.form("add_event", clear_on_submit=True):
        ec1, ec2 = st.columns((1, 3))
        etype = ec1.selectbox("Type", list(EVENT_TYPES))
        ebody = ec2.text_input("Event note")
        if st.form_submit_button("Add event"):
            if ebody.strip():
                try:
                    add_research_event(pid, body=ebody.strip(), event_type=etype)
                    st.success("Event added.")
                    st.rerun()
                except SensitiveCredentialError as e:
                    st.error(str(e))
            else:
                st.error("Event note required.")
    if not events:
        empty_state("No timeline events", "Log diligence steps, links, and stage changes here.")
    else:
        for ev in events:
            cols = st.columns((0.2, 0.65, 0.15))
            cols[0].caption(ev.get("event_type") or "note")
            cols[1].write(f"{ev.get('body') or '—'}\n\n_{ev.get('created_at') or ''}_")
            if cols[2].button("✕", key=f"edel_{ev['id']}"):
                delete_research_event(ev["id"])
                st.rerun()

footer("Project Tracker")
