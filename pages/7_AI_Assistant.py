"""AI Assistant — AssistantProvider (rule + OpenAI-compatible); labels; market_provider for prices."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.ai_service import (
    RESEARCH_CHECKLIST,
    answer,
    get_assistant_provider,
    research_template,
)
from mccc.assistant import TIPS
from mccc.auth import get_session_user
from mccc.db import add_note, init_db, list_notes, list_projects, log_event
from mccc.subscriptions import has_pro_feature
from mccc.ui import footer, hero, page_setup, pro_locked_panel, seed_phrase_warning, upgrade_cta

page_setup("ai_assistant", "AI Assistant")
hero(
    "Research Assistant",
    "Rule-based by default; optional OpenAI-compatible API via AI_API_KEY. "
    "Never invents live prices — market questions use market_provider (LIVE/DEMO).",
)
seed_phrase_warning()

init_db()
user = get_session_user()
uid = user.get("id") if user else None

provider = get_assistant_provider(prefer_llm=True)
st.caption(f"Active provider factory default: `{provider.name}` (toggle LLM below may still fall back to rule).")

tab_ask, tab_check, tab_note, tab_tips = st.tabs(
    ["Ask", "Research checklist", "Structure a note", "All tips"]
)

with tab_ask:
    q = st.text_input(
        "Ask about workflow / diligence / airdrops / security / markets",
        placeholder="e.g. airdrop eligibility hygiene · ETH price",
    )
    use_llm = st.toggle("Try optional LLM if AI_API_KEY set", value=True)
    st.info(
        "Labels: **FACT** / **DATA** / **ANALYSIS** / **SPECULATION**. "
        "Secrets are refused. Market numbers come only from market_provider when asked."
    )
    if st.button("Get answer", type="primary") and q.strip():
        result = answer(q, use_llm=use_llm, user_id=uid)
        mode = result.get("mode", "rule_based")
        prov = result.get("provider", mode)
        if mode == "refusal":
            st.error(result["answer"])
        elif mode == "llm":
            st.success(f"Mode: LLM · provider=`{prov}`")
            st.markdown(result["answer"])
        else:
            st.info(f"Mode: rule-based · provider=`{prov}`")
            st.markdown(result["answer"])
        labels = result.get("labels") or []
        if labels:
            st.caption("Label set: " + " · ".join(labels))
        for tip in result.get("tips") or []:
            with st.expander(tip["title"]):
                st.markdown(tip["body"])
        log_event("assistant_query", page_key="ai_assistant", meta=(q or "")[:80])
        st.caption("ai_usage logged for this answer.")

with tab_check:
    st.markdown("Use this checklist before treating any narrative as research-complete.")
    for i, item in enumerate(RESEARCH_CHECKLIST):
        st.checkbox(item, key=f"ai_check_{i}")
    st.caption("Checkboxes are session-local UX only — not stored as fake completion metrics.")

with tab_note:
    topic = st.text_input("Topic", placeholder="Bridge risk on DEMO L2")
    context = st.text_area("Case context (optional)")
    projects = list_projects()
    link_opts = {"(none)": None}
    for p in projects:
        link_opts[f"#{p['id']} {p['name']}"] = p["id"]
    link_pick = st.selectbox("Optional project link", list(link_opts.keys()))
    if st.button("Generate structured note", type="primary"):
        note = research_template(topic or "Untitled", context)
        st.session_state["draft_note"] = note
    draft = st.session_state.get("draft_note")
    if draft:
        st.markdown(draft["body"])
        st.caption("Structured with FACT/DATA/ANALYSIS/SPECULATION labels + checklist.")
        if st.button("Save note to SQLite"):
            add_note(draft["title"], draft["body"], draft["tags"], project_id=link_opts[link_pick])
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
if has_pro_feature("pro_ai_deep_research", user_id=uid):
    st.success("PRO deep-research checklists unlocked (still labelled; still local).")
    st.markdown(
        "- Extended: competitor matrix\n"
        "- Extended: token unlock calendar template\n"
        "- Extended: incident-response reading list\n"
    )
else:
    pro_locked_panel("Extended research checklists")

footer("AI Assistant")
