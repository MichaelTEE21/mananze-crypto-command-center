"""AI Assistant — wired to ai_service (rule-based + optional LLM)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.ai_service import answer, research_template
from mccc.assistant import TIPS
from mccc.auth import get_session_user
from mccc.db import add_note, init_db, is_feature_enabled, list_notes, log_event
from mccc.ui import hero, page_setup, pro_locked_panel, seed_phrase_warning

page_setup("ai_assistant", "AI Assistant")
hero(
    "Research Assistant",
    "Rule-based by default; optional OpenAI-compatible API via AI_API_KEY. Never invents live prices.",
)
seed_phrase_warning()

init_db()
user = get_session_user()
uid = user.get("id") if user else None

tab_ask, tab_note, tab_tips = st.tabs(["Ask", "Structure a note", "All tips"])

with tab_ask:
    q = st.text_input(
        "Ask about workflow / diligence / airdrops / security / markets",
        placeholder="e.g. airdrop eligibility hygiene",
    )
    use_llm = st.toggle("Try optional LLM if AI_API_KEY set", value=True)
    if st.button("Get answer", type="primary") and q.strip():
        result = answer(q, use_llm=use_llm, user_id=uid)
        mode = result.get("mode", "rule_based")
        if mode == "refusal":
            st.error(result["answer"])
        elif mode == "llm":
            st.success("Mode: LLM (OpenAI-compatible)")
            st.markdown(result["answer"])
        else:
            st.info("Mode: rule-based (local)")
            st.markdown(result["answer"])
        for tip in result.get("tips") or []:
            with st.expander(tip["title"]):
                st.markdown(tip["body"])
        log_event("assistant_query", page_key="ai_assistant", meta=(q or "")[:80])

with tab_note:
    topic = st.text_input("Topic", placeholder="Bridge risk on DEMO L2")
    context = st.text_area("Case context (optional)")
    if st.button("Generate structured note", type="primary"):
        note = research_template(topic or "Untitled", context)
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
    st.success("PRO deep-research checklists unlocked (still labelled; still local).")
    st.markdown(
        "- Extended: competitor matrix\n"
        "- Extended: token unlock calendar template\n"
        "- Extended: incident-response reading list\n"
    )
else:
    pro_locked_panel("Extended research checklists")
