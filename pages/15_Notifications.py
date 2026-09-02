"""In-app notifications inbox."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.notifications import (
    create,
    dismiss,
    list_notifications,
    mark_all_read,
    mark_read,
    mark_unread,
    unread_count,
)
from mccc.ui import empty_state, error_banner, hero, metric_card, page_setup, session_user_id, footer

page_setup("notifications", "Notifications")
hero("Notifications", "Local inbox — alerts, system notes, research reminders.")

uid = session_user_id()
unread = unread_count(user_id=uid)
metric_card(str(unread), "Unread")

c1, c2 = st.columns(2)
with c1:
    if st.button("Mark all read", use_container_width=True):
        mark_all_read(user_id=uid)
        st.rerun()
with c2:
    show_unread = st.toggle("Unread only", value=False)

st.subheader("Compose (local)")
with st.form("compose_note", clear_on_submit=True):
    title = st.text_input("Title")
    body = st.text_area("Body")
    category = st.selectbox("Category", ["general", "alert", "system", "research"])
    if st.form_submit_button("Create", type="primary"):
        try:
            create(title, body=body, category=category, user_id=uid)
            st.success("Created.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

rows = list_notifications(user_id=uid, unread_only=show_unread)
st.subheader(f"Inbox ({len(rows)})")
if not rows:
    empty_state("Inbox empty", "Alert checks and system notes will appear here.")
else:
    for n in rows:
        with st.container():
            badge = "UNREAD" if not n.get("read") else "read"
            st.markdown(f"**{n['title']}** · `{n.get('category')}` · _{badge}_")
            if n.get("body"):
                st.write(n["body"])
            st.caption(n.get("created_at") or "")
            a, b, c = st.columns(3)
            if a.button("Mark read", key=f"mr_{n['id']}", disabled=bool(n.get("read"))):
                mark_read(n["id"])
                st.rerun()
            if b.button("Mark unread", key=f"mu_{n['id']}", disabled=not bool(n.get("read"))):
                mark_unread(n["id"])
                st.rerun()
            if c.button("Dismiss", key=f"di_{n['id']}"):
                dismiss(n["id"])
                st.rerun()
            st.divider()

footer("Notifications")
