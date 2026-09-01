"""Stage 7 — Local rule-based research assistant (no LLM, no invented prices)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.assistant import TIPS, match_tips, structure_research_note
from mccc.db import add_note, init_db, is_feature_enabled, list_notes, log_event
from mccc.ui import hero, page_setup, pro_locked_panel

page_setup("ai_assistant", "AI Assistant")
hero(
    "Research Assistant",
    "Local rule-based checklists & note structuring — no LLM, no invented live prices.",
)

init_db()

tab_ask, tab_note, tab_tips = st.tabs(["Ask", "Structure a note", "All tips"])

with tab_ask:
    q = st.text_input("Ask about workflow / diligence / airdrops / security / markets", placeholder="e.g. airdrop eligibility hygiene")
    if st.button("Get checklist", type="primary") or q:
        tips = match_tips(q or "workflow")
        for tip in tips:
            with st.expander(tip["title"], expanded=True):
                st.markdown(tip["body"])
        log_event("assistant_query", page_key="ai_assistant", meta=(q or "")[:80])

with tab_note:
    topic = st.text_input("Topic", placeholder="Bridge risk on DEMO L2")
    context = st.text_area("Case context (optional)")
    if st.button("Generate structured note", type="primary"):
        note = structure_research_note(topic or "Untitled", context)
        st.session_state["draft_note"] = note
    draft = st.session_state.get("draft_note")
    if draft:
        st.markdown(draft["body"])
        if st.button("Save note to SQLite"):
            add_note(draft["title"], draft["body"], draft["tags"])
            log_event("case_opened", page_key="ai_assistant", meta=draft["title"][:80])
            st.success("Saved.")
    st.subheader("Saved research notes")
    notes = list_notes()
    if not notes:
        st.caption("No notes yet.")
    else:
        for n in notes[:10]:
            with st.expander(n["title"]):
                st.markdown(n["body"])

with tab_tips:
    for tip in TIPS:
        with st.expander(tip["title"]):
            st.markdown(tip["body"])

st.divider()
if is_feature_enabled("pro_ai_deep_research"):
    st.success("PRO deep-research checklists unlocked (still rule-based, still local).")
    st.markdown(
        "- Extended: competitor matrix\n"
        "- Extended: token unlock calendar template\n"
        "- Extended: incident-response reading list\n"
    )
else:
    pro_locked_panel("Extended research checklists")
