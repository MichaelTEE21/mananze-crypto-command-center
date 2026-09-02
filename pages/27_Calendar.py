"""Crypto Calendar — Phase 1 foundation (schema + Month/List + filters). Live feeds = later phases."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.calendar_service import (
    CALENDAR_EVENT_TYPES,
    EVENT_TYPE_LABELS,
    ensure_ready,
    events_for_month,
    intelligence_hook,
    list_events,
    month_grid,
    parse_year_month,
)
from mccc.ui import demo_callout, empty_state, footer, hero, page_setup, section_header, status_badge

page_setup("calendar", "Calendar")
hero(
    "CALENDAR",
    "Foundation · airdrops / unlocks / burns / project / governance / important — population in Phase 2–3",
)
st.caption(
    "Events are local SQLite rows. DEMO seeds are labelled. "
    "Do not treat empty unlock/burn feeds as zero activity — they are not wired yet."
)
demo_callout("Full burn/unlock/airdrop population = Phase 2–3. This page is architecture + UX shell.")

ensure_ready()

view = st.radio("View", ["Month", "List"], horizontal=True)
type_filter = st.selectbox(
    "Filter by type",
    ["(all)"] + list(CALENDAR_EVENT_TYPES),
    format_func=lambda x: "All types" if x == "(all)" else EVENT_TYPE_LABELS.get(x, x),
)
ym = st.text_input("Month (YYYY-MM)", value=f"{parse_year_month()[0]:04d}-{parse_year_month()[1]:02d}")
year, month = parse_year_month(ym)
etype = None if type_filter == "(all)" else type_filter

events = events_for_month(year, month, event_type=etype)
if etype and view == "List":
    events = list_events(event_type=etype, month=f"{year:04d}-{month:02d}")

section_header(f"{year:04d}-{month:02d}", f"{len(events)} event(s) in view")

if view == "Month":
    by_day: dict[str, list] = {}
    for ev in events:
        d = (ev.get("event_date") or "")[:10]
        by_day.setdefault(d, []).append(ev)
    grid = month_grid(year, month)
    st.caption("Mon — Tue — Wed — Thu — Fri — Sat — Sun")
    for week in grid:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day is None:
                    st.write(" ")
                else:
                    key = day.isoformat()
                    day_events = by_day.get(key, [])
                    label = f"**{day.day}**"
                    if day_events:
                        label += f" · {len(day_events)}"
                    st.markdown(label)
                    for ev in day_events[:3]:
                        demo = " DEMO" if ev.get("is_demo") else ""
                        st.caption(f"{ev.get('event_type')}{demo}: {(ev.get('title') or '')[:28]}")
else:
    if not events:
        empty_state(
            "No events this month",
            "DEMO seeds appear on first run. Live unlock/burn/airdrop feeds arrive in Phase 2–3.",
        )
    for ev in events:
        demo = "DEMO" if ev.get("is_demo") else "LOCAL"
        status_badge(demo, "demo" if ev.get("is_demo") else "info")
        status_badge(ev.get("event_type") or "?", "warn")
        st.markdown(
            f"**{ev.get('title')}** · `{ev.get('event_date')}`"
            + (f" → `{ev.get('end_date')}`" if ev.get("end_date") else "")
        )
        st.caption(
            f"Source: {ev.get('source') or '—'} · quality: {ev.get('data_quality') or 'UNKNOWN'} · "
            f"{(ev.get('description') or '')[:180]}"
        )
        hook = intelligence_hook(ev)
        if hook:
            if st.button(f"ANALYSE {hook['intel_report_q']}", key=f"cal_analyse_{ev['id']}"):
                st.session_state["intel_report_q"] = hook["intel_report_q"]
                st.session_state["mccc_analyse_entity_hint"] = hook["mccc_analyse_entity_hint"]
                st.switch_page("pages/24_Intelligence_Center.py")
        st.divider()

footer("Calendar")
