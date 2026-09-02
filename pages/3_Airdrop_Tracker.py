"""Airdrop Tracker — statuses, dashboard, filters, tasks."""
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
    normalize_airdrop_status,
    update_airdrop,
)
from mccc.security import SensitiveCredentialError, reject_sensitive_credential
from mccc.subscriptions import check_limit, require_can_add
from mccc.ui import demo_callout, empty_state, footer, hero, metric_card, page_setup, section_header, status_badge, session_user_id, upgrade_cta

page_setup("airdrop_tracker", "Airdrop Tracker")
hero("Airdrop Tracker", "Campaigns, eligibility notes, statuses, and task checklists.")
demo_callout("DEMO seed airdrops are examples for research practice — not live eligibility claims.")

init_db()
_uid = session_user_id()
_ad_gate = check_limit("airdrops", user_id=_uid)
if _ad_gate.get("upgrade_cta"):
    st.warning(_ad_gate["message"])
    upgrade_cta(_ad_gate["message"])
elif not _ad_gate.get("unlimited"):
    st.caption(_ad_gate["message"])

STATUS_KIND = {
    "DISCOVERED": "info",
    "RESEARCHING": "info",
    "ACTIVE": "success",
    "COMPLETED": "success",
    "WAITING": "warn",
    "CLAIMED": "success",
    "MISSED": "danger",
    "ARCHIVED": "danger",
}

ACTIVE_SET = {"DISCOVERED", "RESEARCHING", "ACTIVE", "WAITING"}
DONE_SET = {"COMPLETED", "CLAIMED"}
MISSED_SET = {"MISSED"}


def _safe(text: str, field: str) -> str:
    return reject_sensitive_credential(text or "", field=field)


with st.expander("Add airdrop", expanded=False):
    with st.form("add_airdrop", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Project name")
        chain = c2.text_input("Chain")
        status = c3.selectbox("Status", list(AIRDROP_STATUSES))
        eligibility = st.text_area("Eligibility notes")
        c4, c5, c6 = st.columns(3)
        value = c4.text_input("Estimated value", value="DEMO / unknown")
        deadline = c5.text_input("Deadline", placeholder="YYYY-MM-DD or TBD")
        start_date = c6.text_input("Start date")
        c7, c8, c9 = st.columns(3)
        token = c7.text_input("Token")
        points = c8.text_input("Points / XP")
        tge_date = c9.text_input("TGE date")
        c10, c11, c12 = st.columns(3)
        claim_page = c10.text_input("Claim page URL")
        official = c11.text_input("Official website")
        docs_url = c12.text_input("Docs URL")
        c13, c14, c15 = st.columns(3)
        funding = c13.text_input("Funding")
        investors = c14.text_input("Investors")
        priority = c15.slider("Priority (1=highest)", 1, 5, 3)
        risk = st.text_input("Risk notes")
        twitter = st.text_input("Twitter / X")
        if st.form_submit_button("Add airdrop", type="primary"):
            if not name.strip():
                st.error("Project name required.")
            else:
                try:
                    require_can_add("airdrops", user_id=_uid)
                    _safe(eligibility, "airdrop.eligibility")
                    _safe(risk, "airdrop.risk")
                    add_airdrop(
                        name,
                        chain,
                        status,
                        eligibility,
                        value,
                        deadline,
                        token=token,
                        points=points,
                        claim_page=claim_page,
                        official_website=official,
                        docs_url=docs_url,
                        start_date=start_date,
                        tge_date=tge_date,
                        funding=funding,
                        investors=investors,
                        risk=risk,
                        priority=priority,
                        twitter=twitter,
                        eligibility=eligibility,
                    )
                    st.success("Airdrop saved.")
                    st.rerun()
                except SensitiveCredentialError as e:
                    st.error(str(e))

rows = list_airdrops()
# Normalize for display
for r in rows:
    r["status"] = normalize_airdrop_status(r.get("status"))

# --- Dashboard ---
section_header("Dashboard", "Active · upcoming deadlines · completed · missed · priority")
active = [r for r in rows if r["status"] in ACTIVE_SET]
completed = [r for r in rows if r["status"] in DONE_SET]
missed = [r for r in rows if r["status"] in MISSED_SET]
with_deadline = [r for r in active if (r.get("deadline") or "").strip() and (r.get("deadline") or "").upper() != "TBD"]
priority_rows = sorted(
    [r for r in active if r.get("priority") is not None],
    key=lambda x: int(x.get("priority") or 99),
)[:5]

d1, d2, d3, d4, d5 = st.columns(5)
with d1:
    metric_card(str(len(active)), "Active / in-flight")
with d2:
    metric_card(str(len(with_deadline)), "Upcoming deadlines")
with d3:
    metric_card(str(len(completed)), "Completed / claimed")
with d4:
    metric_card(str(len(missed)), "Missed")
with d5:
    metric_card(str(len(priority_rows)), "Top priority shown")

if with_deadline:
    with st.expander(f"Upcoming deadlines ({len(with_deadline)})", expanded=True):
        for a in with_deadline[:10]:
            status_badge(a["status"], STATUS_KIND.get(a["status"], "info"))
            st.markdown(
                f"**{a.get('project_name')}** · `{a.get('deadline')}` · "
                f"{a.get('chain') or '—'} · P{a.get('priority') or '—'}"
            )

if priority_rows:
    with st.expander("Priority focus", expanded=False):
        for a in priority_rows:
            st.markdown(
                f"P{a.get('priority')} · **{a.get('project_name')}** · `{a['status']}` · "
                f"{a.get('chain') or '—'}"
            )

# --- Filters ---
fc1, fc2, fc3, fc4 = st.columns(4)
q = fc1.text_input("Search", placeholder="name / chain / token").strip().lower()
status_f = fc2.selectbox("Filter status", ["(all)"] + list(AIRDROP_STATUSES))
chain_f = fc3.text_input("Filter chain").strip().lower()
sort_by = fc4.selectbox("Sort by", ["deadline", "status", "priority", "updated_at", "project_name", "chain"])

filtered = []
for r in rows:
    blob = " ".join(str(v) for v in r.values() if v is not None).lower()
    if q and q not in blob:
        continue
    if status_f != "(all)" and r.get("status") != status_f:
        continue
    if chain_f and chain_f not in (r.get("chain") or "").lower():
        continue
    filtered.append(r)

reverse = sort_by in ("updated_at",)
filtered.sort(key=lambda r: (r.get(sort_by) in (None, ""), r.get(sort_by) or ""), reverse=reverse)

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
        "start_date",
        "tge_date",
        "priority",
        "funding",
        "last_checked",
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
    status_badge(cur["status"], STATUS_KIND.get(cur["status"], "info"))

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
        notes = st.text_area(
            "Eligibility notes",
            value=cur.get("eligibility_notes") or cur.get("eligibility") or "",
        )
        value = st.text_input("Estimated value", value=cur["estimated_value"] or "DEMO / unknown")
        c1, c2, c3 = st.columns(3)
        deadline = c1.text_input("Deadline", value=cur["deadline"] or "")
        start_date = c2.text_input("Start", value=cur.get("start_date") or "")
        tge_date = c3.text_input("TGE", value=cur.get("tge_date") or "")
        c4, c5, c6 = st.columns(3)
        token = c4.text_input("Token", value=cur.get("token") or "")
        points = c5.text_input("Points / XP", value=cur.get("points") or "")
        priority = c6.slider("Priority", 1, 5, int(cur.get("priority") or 3))
        c7, c8, c9 = st.columns(3)
        claim_page = c7.text_input("Claim page", value=cur.get("claim_page") or "")
        official = c8.text_input("Official website", value=cur.get("official_website") or "")
        docs_url = c9.text_input("Docs", value=cur.get("docs_url") or "")
        c10, c11, c12 = st.columns(3)
        funding = c10.text_input("Funding", value=cur.get("funding") or "")
        investors = c11.text_input("Investors", value=cur.get("investors") or "")
        last_checked = c12.text_input("Last checked", value=cur.get("last_checked") or "")
        risk = st.text_input("Risk", value=cur.get("risk") or "")
        twitter = st.text_input("Twitter / X", value=cur.get("twitter") or "")
        a, b = st.columns(2)
        if a.form_submit_button("Save", type="primary"):
            try:
                _safe(notes, "airdrop.eligibility")
                _safe(risk, "airdrop.risk")
                update_airdrop(
                    aid,
                    project_name=name,
                    chain=chain,
                    status=status,
                    eligibility_notes=notes,
                    eligibility=notes,
                    estimated_value=value,
                    deadline=deadline,
                    start_date=start_date,
                    tge_date=tge_date,
                    token=token,
                    points=points,
                    claim_page=claim_page,
                    official_website=official,
                    docs_url=docs_url,
                    funding=funding,
                    investors=investors,
                    risk=risk,
                    last_checked=last_checked,
                    priority=priority,
                    twitter=twitter,
                )
                st.success("Updated.")
                st.rerun()
            except SensitiveCredentialError as e:
                st.error(str(e))
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
                try:
                    _safe(ttitle, "airdrop.task")
                    add_task(aid, ttitle.strip())
                    st.rerun()
                except SensitiveCredentialError as e:
                    st.error(str(e))
    if not tasks:
        empty_state("No tasks", "Break eligibility work into checklist items.")
    else:
        done_n = sum(1 for t in tasks if t["done"])
        st.caption(f"{done_n} / {len(tasks)} tasks done")
        for t in tasks:
            cols = st.columns((0.15, 0.7, 0.15))
            done = cols[0].checkbox(
                "Done",
                value=bool(t["done"]),
                key=f"task_{t['id']}",
                label_visibility="collapsed",
            )
            if done != bool(t["done"]):
                toggle_done(t["id"], done=done)
                st.rerun()
            cols[1].write(t["title"])
            if cols[2].button("✕", key=f"tdel_{t['id']}"):
                delete_task(t["id"])
                st.rerun()

footer("Airdrop Tracker")
