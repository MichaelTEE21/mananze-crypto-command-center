"""Global research notes workspace — filter by project, timeline linkage."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.bookmarks import is_favourite, toggle_favourite
from mccc.db import add_note, init_db, list_notes, list_projects
from mccc.research import add_research_event, list_research_events
from mccc.security import SensitiveCredentialError, reject_sensitive_credential
from mccc.ui import empty_state, error_banner, hero, page_setup, section_header, seed_phrase_warning, footer

page_setup("research", "Research")
hero(
    "Research workspace",
    "Global notes + optional project filter. Timeline events stay on the project; notes can link via project_id.",
)

init_db()
seed_phrase_warning()

projects = list_projects()
proj_opts = {"(all notes)": None, "(unlinked)": -1}
for p in projects:
    proj_opts[f"#{p['id']} {p['name']}"] = p["id"]

filt = st.selectbox("Filter by project", list(proj_opts.keys()))
pid_filter = proj_opts[filt]

section_header("Add note")
with st.form("add_research_note", clear_on_submit=True):
    title = st.text_input("Title")
    body = st.text_area("Body")
    tags = st.text_input("Tags", placeholder="defi, bridge")
    link_opts = {"(none)": None}
    for p in projects:
        link_opts[f"#{p['id']} {p['name']}"] = p["id"]
    link_pick = st.selectbox("Link to project", list(link_opts.keys()))
    also_timeline = st.checkbox("Also append a research_events timeline row", value=False)
    if st.form_submit_button("Save note", type="primary"):
        try:
            reject_sensitive_credential(body or "", field="note.body")
            reject_sensitive_credential(title or "", field="note.title")
            nid = add_note(title, body, tags, project_id=link_opts[link_pick])
            if also_timeline and link_opts[link_pick]:
                add_research_event(link_opts[link_pick], body=f"Note #{nid}: {title}", event_type="note")
            st.success(f"Saved note #{nid}.")
            st.rerun()
        except SensitiveCredentialError as exc:
            error_banner(str(exc))
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

notes = list_notes()
if pid_filter == -1:
    notes = [n for n in notes if not n.get("project_id")]
elif pid_filter is not None:
    notes = [n for n in notes if n.get("project_id") == pid_filter]

section_header(f"Notes ({len(notes)})")
if not notes:
    empty_state("No notes for this filter", "Add a note above or clear the project filter.")
else:
    for n in notes[:50]:
        fav = is_favourite("note", str(n["id"]))
        with st.expander(f"{n['title']} · project_id={n.get('project_id') or '—'}"):
            st.markdown(n.get("body") or "")
            st.caption(f"tags={n.get('tags') or '—'} · updated={n.get('updated_at')}")
            b1, b2 = st.columns(2)
            if b1.button("★" if fav else "☆ Bookmark", key=f"bm_note_{n['id']}"):
                toggle_favourite("note", str(n["id"]))
                st.rerun()
            if n.get("project_id") and b2.button("Show timeline", key=f"tl_{n['id']}"):
                events = list_research_events(int(n["project_id"]), limit=10)
                if not events:
                    st.caption("No timeline events yet.")
                else:
                    for e in events:
                        st.markdown(f"- `{e['event_type']}` {e.get('body','')[:120]} · {e.get('created_at')}")

footer("Research")
