"""User Analytics — aggregate local usage + command-center counts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

from mccc.db import (
    connect,
    init_db,
    list_airdrops,
    list_projects,
    list_wallets,
    usage_summary,
)
from mccc.portfolio import list_assets
from mccc.ui import empty_state, hero, metric_card, page_setup, session_user_id
from mccc.watchlist import list_items

page_setup("user_analytics", "User Analytics")
hero(
    "User Analytics",
    "Local SQLite aggregates — page views, research inventory, AI usage. No PII required.",
)

init_db()
uid = session_user_id()
summary = usage_summary()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card(str(summary["total_events"]), "Total events")
with c2:
    metric_card(str(len(list_projects())), "Projects")
with c3:
    metric_card(str(len(list_airdrops())), "Airdrops")
with c4:
    metric_card(str(len(list_assets(user_id=uid))), "Portfolio assets")

c5, c6, c7 = st.columns(3)
with c5:
    metric_card(str(len(list_wallets())), "Wallets")
with c6:
    metric_card(str(len(list_items(user_id=uid))), "Watchlist")
with c7:
    with connect() as conn:
        ai_n = conn.execute("SELECT COUNT(*) AS c FROM ai_usage").fetchone()["c"]
        notif_n = conn.execute("SELECT COUNT(*) AS c FROM notifications").fetchone()["c"]
    metric_card(str(ai_n), f"AI calls · {notif_n} notifs")

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
    empty_state("No page views yet", "Navigate the app to accumulate local stats.")

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

with connect() as conn:
    ai_rows = conn.execute(
        "SELECT kind, COUNT(*) AS c, SUM(tokens_est) AS tokens FROM ai_usage GROUP BY kind"
    ).fetchall()
if ai_rows:
    st.subheader("AI usage")
    st.dataframe(pd.DataFrame([dict(r) for r in ai_rows]), use_container_width=True, hide_index=True)

st.caption("Data stays on this machine in data/mccc.db — nothing is phoned home.")
