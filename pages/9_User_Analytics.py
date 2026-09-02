"""User Analytics — page views, feature usage, referrals, lessons, resource clicks. No PII."""
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
from mccc.education import completed_keys, list_lessons
from mccc.partners import click_analytics
from mccc.portfolio import list_assets
from mccc.resources import list_resources
from mccc.ui import empty_state, hero, metric_card, page_setup, session_user_id, footer
from mccc.watchlist import list_items

page_setup("user_analytics", "User Analytics")
hero(
    "User Analytics",
    "Local SQLite aggregates — page views, feature usage, partner referral clicks, "
    "lesson completions, resource clicks. No PII.",
)

init_db()
uid = session_user_id()
summary = usage_summary()
lessons = list_lessons()
done = completed_keys(user_id=uid)
partner_stats = click_analytics()
resources = list_resources()
resource_clicks = sum(int(r.get("click_count") or 0) for r in resources)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card(str(summary["total_events"]), "Total events")
with c2:
    metric_card(str(len(list_projects())), "Projects")
with c3:
    metric_card(str(len(list_airdrops())), "Airdrops")
with c4:
    metric_card(str(len(list_assets(user_id=uid))), "Portfolio assets")

c5, c6, c7, c8 = st.columns(4)
with c5:
    metric_card(str(len(list_wallets())), "Wallets")
with c6:
    metric_card(str(len(list_items(user_id=uid))), "Watchlist")
with c7:
    with connect() as conn:
        ai_n = conn.execute("SELECT COUNT(*) AS c FROM ai_usage").fetchone()["c"]
        notif_n = conn.execute("SELECT COUNT(*) AS c FROM notifications").fetchone()["c"]
    metric_card(str(ai_n), f"AI calls · {notif_n} notifs")
with c8:
    metric_card(f"{len(done)}/{len(lessons)}", "Lessons marked complete")

c9, c10 = st.columns(2)
with c9:
    metric_card(str(partner_stats.get("total_clicks", 0)), "Partner referral clicks")
with c10:
    metric_card(str(resource_clicks), "Resource click_count sum")

st.info(
    "**Privacy:** Analytics stay on this machine (`data/mccc.db`). "
    "No emails, names, IP addresses, or wallet private keys are collected here. "
    "Partner click rows store link id / category / source_page / timestamp only."
)

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

st.subheader("Feature usage (by event type)")
if summary["by_type"]:
    st.dataframe(
        pd.DataFrame(summary["by_type"]).rename(columns={"event_type": "Type", "c": "Count"}),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Partner referral clicks")
st.caption("Aggregated only — no user identity.")
pc = partner_stats.get("per_category") or {}
if pc:
    st.dataframe(
        pd.DataFrame([{"category": k, "clicks": v} for k, v in pc.items()]),
        use_container_width=True,
        hide_index=True,
    )
pp = partner_stats.get("per_platform") or []
if pp:
    st.dataframe(pd.DataFrame(pp), use_container_width=True, hide_index=True)

st.subheader("Lesson completion (marked only)")
st.caption("Honest: count of lessons you marked complete vs lessons on disk — no invented rates.")
st.write(f"Completed keys: {', '.join(sorted(done)) if done else '(none)'}")

st.subheader("Resources (click_count)")
if resources:
    rdf = pd.DataFrame(resources)
    cols = [c for c in ("id", "title", "resource_type", "is_official", "click_count", "url") if c in rdf.columns]
    st.dataframe(rdf[cols], use_container_width=True, hide_index=True)
else:
    st.caption("No resources yet — add via Admin.")

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

footer("User Analytics")
