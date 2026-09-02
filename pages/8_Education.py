"""Education platform — categorized lessons, quiz, glossary, progress (honest counts)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.bookmarks import is_favourite, toggle_favourite
from mccc.education import (
    CATEGORIES,
    completed_keys,
    lessons_by_category,
    list_lessons,
    score_quiz,
    upsert_progress,
)
from mccc.paths import ensure_dirs
from mccc.ui import empty_state, hero, metric_card, page_setup, section_header, session_user_id, footer

page_setup("education", "Academy")
hero(
    "Academy",
    "BEGINNER → INTERMEDIATE → ADVANCED local lessons. Progress is what you mark — no fake completion metrics.",
)

ensure_dirs()
uid = session_user_id()
lessons = list_lessons()
done = completed_keys(user_id=uid)
by_cat = lessons_by_category()

if not lessons:
    empty_state("No lessons found", "Add markdown under content/education/")
    st.stop()

# Honest progress only: marked-complete / available lessons
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card(f"{len(done)} / {len(lessons)}", "Marked complete")
with c2:
    metric_card(str(len(by_cat.get("BEGINNER") or [])), "Beginner modules")
with c3:
    metric_card(str(len(by_cat.get("INTERMEDIATE") or [])), "Intermediate")
with c4:
    metric_card(str(len(by_cat.get("ADVANCED") or [])), "Advanced")

st.caption(
    "Counts reflect lessons on disk and rows you marked complete in SQLite — nothing is invented."
)

cat_filter = st.radio("Category", ["ALL", *CATEGORIES], horizontal=True)
if cat_filter == "ALL":
    pool = lessons
else:
    pool = by_cat.get(cat_filter) or []

if not pool:
    empty_state(f"No {cat_filter} lessons", "Add markdown or adjust category frontmatter.")
    st.stop()

labels = [f"[{L['category']}] {L['title']}" + (" ✓" if L["key"] in done else "") for L in pool]
pick = st.selectbox("Module", labels)
lesson = pool[labels.index(pick)]
key = lesson["key"]

section_header(lesson["title"], f"{lesson['category']} · `{key}`")

# Bookmarks
fav = is_favourite("lesson", key)
if st.button("★ Favourited" if fav else "☆ Bookmark lesson"):
    toggle_favourite("lesson", key)
    st.rerun()

# Warnings
if lesson.get("warnings"):
    with st.expander("Warnings / disclaimers", expanded=True):
        for w in lesson["warnings"]:
            st.warning(w)

# Body (explanation)
st.markdown(lesson["body"])

# Glossary
if lesson.get("glossary"):
    with st.expander("Glossary snippet"):
        for term, definition in lesson["glossary"].items():
            st.markdown(f"**{term}** — {definition}")

# Knowledge check
quiz = lesson.get("quiz") or []
if quiz:
    section_header("Knowledge check", "Local quiz — score only from your answers")
    answers: list[int] = []
    for i, item in enumerate(quiz):
        choice = st.radio(item["q"], item["choices"], key=f"quiz_{key}_{i}")
        answers.append(item["choices"].index(choice))
    if st.button("Check answers", key=f"check_{key}"):
        sc = score_quiz(key, answers)
        if sc is None:
            st.info("No scoreable quiz for this lesson.")
        else:
            st.success(f"Score: {sc:.0%} ({sum(1 for i,a in enumerate(answers) if a == quiz[i]['answer'])}/{len(quiz)})")
            upsert_progress(key, completed=(key in done) or sc >= 1.0, quiz_score=sc, user_id=uid)

# Related
related_keys = lesson.get("related") or []
if related_keys:
    section_header("Related lessons")
    key_to_title = {L["key"]: L["title"] for L in lessons}
    for rk in related_keys:
        mark = " ✓" if rk in done else ""
        st.markdown(f"- `{rk}` — {key_to_title.get(rk, rk)}{mark}")

# Progress actions
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

footer("Education")
