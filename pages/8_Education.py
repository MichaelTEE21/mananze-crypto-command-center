"""Education modules with progress tracking."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.education import completed_keys, upsert_progress
from mccc.paths import EDUCATION_DIR, ensure_dirs
from mccc.ui import empty_state, hero, metric_card, page_setup, session_user_id

page_setup("education", "Education")
hero("Education", "Crypto research basics + security — static local lessons. Not financial advice.")

ensure_dirs()
uid = session_user_id()
lessons = sorted(EDUCATION_DIR.glob("*.md"))
done = completed_keys(user_id=uid)

if not lessons:
    empty_state("No lessons found", "Add markdown under content/education/")
else:
    metric_card(f"{len(done)} / {len(lessons)}", "Lessons marked complete")
    titles = [p.stem.replace("_", " ").title() for p in lessons]
    pick = st.selectbox("Module", titles)
    path = lessons[titles.index(pick)]
    key = path.stem
    st.markdown(path.read_text(encoding="utf-8"))
    completed = key in done
    st.caption("✓ Completed" if completed else "Not marked complete yet")
    c1, c2 = st.columns(2)
    if c1.button("Mark complete", type="primary", disabled=completed):
        upsert_progress(key, completed=True, user_id=uid)
        st.success("Progress saved.")
        st.rerun()
    if c2.button("Mark incomplete", disabled=not completed):
        upsert_progress(key, completed=False, user_id=uid)
        st.rerun()
