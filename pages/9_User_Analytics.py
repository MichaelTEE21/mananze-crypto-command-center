"""Stage 9 — Local usage analytics (privacy-friendly)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

from mccc.db import init_db, usage_summary
from mccc.ui import hero, page_setup

page_setup("user_analytics", "User Analytics")
hero(
    "User Analytics",
    "Local SQLite usage stats — pages visited & cases opened. No PII required.",
)

init_db()
summary = usage_summary()

c1, c2, c3 = st.columns(3)
c1.metric("Total events", summary["total_events"])
c2.metric("Page types tracked", len(summary["by_page"]))
c3.metric("Event types", len(summary["by_type"]))

st.subheader("Page views")
if summary["by_page"]:
    df = pd.DataFrame(summary["by_page"])
    fig = px.bar(
        df,
        x="page_key",
        y="c",
        title="Page views (local)",
        template="plotly_dark",
        labels={"c": "Count", "page_key": "Page"},
    )
    fig.update_layout(paper_bgcolor="#0b0f14", plot_bgcolor="#141a22")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        df.rename(columns={"page_key": "Page", "c": "Views"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No page views yet — navigate the app to accumulate local stats.")

st.subheader("By event type")
if summary["by_type"]:
    st.dataframe(
        pd.DataFrame(summary["by_type"]).rename(columns={"event_type": "Type", "c": "Count"}),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Recent events")
if summary["recent"]:
    st.dataframe(pd.DataFrame(summary["recent"]), use_container_width=True, hide_index=True)

st.caption("Data stays on this machine in data/mccc.db — nothing is phoned home.")
