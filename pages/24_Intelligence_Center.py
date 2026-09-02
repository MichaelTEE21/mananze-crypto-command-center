"""MCCC Intelligence Center — sourced research signals (not a chatbot)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.bookmarks import set_favourite
from mccc.db import add_project, init_db
from mccc.intelligence import DISCLAIMER, IntelligencePipeline, IntelligenceRepository
from mccc.intelligence.schema import CATEGORY_LABELS, EventCategory, EventStatus
from mccc.intelligence.source_service import ROBOTS_TOS_STANCE
from mccc.intelligence.report import REPORT_DISCLAIMER as REPORT_DISCLAIMER_TXT
from mccc.intelligence.report.engine import ReportEngine
from mccc.intelligence.report.schema import SUPPORTED_ENTITY_TYPES
from mccc.intelligence.report.ui_render import (
    render_journey_strip,
    render_report,
    render_security_block,
)
from mccc.ui import (
    data_mode_chip,
    demo_callout,
    empty_state,
    footer,
    hero,
    page_setup,
    section_header,
    session_user_id,
    status_badge,
)

page_setup("intelligence_center", "Intelligence Center")
hero(
    "SEARCH → ANALYSE → UNDERSTAND",
    "MCCC Intelligence Center · sourced signals + Intelligence Reports · not financial advice",
)

init_db()
uid = session_user_id()
repo = IntelligenceRepository()
pipeline = IntelligencePipeline()
pipeline.ensure_ready()


st.info(DISCLAIMER)
demo_callout(
    "DEMO / SYNTHETIC rows are always labelled. Live RSS is optional and never mixed without badges."
)

tab_analyse, tab_feed = st.tabs(["Analyse · Intelligence Report", "Feed · Sourced events"])

with tab_analyse:
    render_journey_strip()
    st.markdown("### ANALYZE A PUBLIC WALLET — or any supported on-chain entity")
    st.caption(
        "PASTE A WALLET. SEE THE STORY BEHIND THE ADDRESS. "
        "Public trail may include transactions, token movements, protocol interactions, and activity over time "
        "when providers respond. Outcome: help answer “What is this wallet actually doing on-chain?” — not what to buy/sell."
    )
    render_security_block()
    st.caption(REPORT_DISCLAIMER_TXT)

    ent = st.selectbox(
        "Entity type",
        ["auto"] + sorted(SUPPORTED_ENTITY_TYPES),
        help="auto detects wallets/tokens/protocols when possible",
    )
    chain = st.selectbox("Chain hint", ["ethereum", "arbitrum", "base", "optimism", "polygon", "solana", "other"])
    q = st.text_input(
        "Search the blockchain / research store",
        placeholder="0x… public address · bitcoin · uniswap · rwa: treasuries · project name",
        key="intel_report_q",
    )
    beginner_mode = st.toggle("Beginner Mode", value=True, key="intel_report_beginner")
    go = st.button("ANALYSE →", type="primary", key="intel_report_go")
    if go and q.strip():
        engine = ReportEngine()
        hint = None if ent == "auto" else ent
        with st.spinner("Analysing public / labelled data…"):
            report = engine.analyse(q.strip(), entity_type_hint=hint, chain=chain)
        st.session_state["mccc_last_intel_report"] = report
    report = st.session_state.get("mccc_last_intel_report")
    if report is not None:
        render_report(report, beginner_mode=beginner_mode)
        st.page_link("pages/7_AI_Assistant.py", label="Ask AI about this report", icon="🤖")
        st.page_link("pages/25_RWA_Intelligence.py", label="Open RWA vertical", icon="🏛️")
    else:
        empty_state(
            "WHAT DO YOU WANT TO UNDERSTAND?",
            "Search a wallet, token, contract, project, protocol, or RWA entity — then ANALYSE →",
        )

with tab_feed:
    st.caption("Sourced research signal feed (Intelligence Agent Phase 1) — engine ≠ chatbot. Scroll sections below.")

# --- Feed (shared below tabs for Phase-1 compatibility) ---
st.divider()
st.markdown("#### Feed · What's happening in crypto right now?")


with st.expander("Sources & ingestion stance", expanded=False):
    st.caption(ROBOTS_TOS_STANCE)
    cols = st.columns(3)
    with cols[0]:
        run_demo = st.button("Refresh DEMO seed", use_container_width=True)
    with cols[1]:
        run_live = st.button("Try live RSS (soft-fail)", use_container_width=True)
    with cols[2]:
        st.caption("Cron architecture via ingestion_runs — no Vercel worker assumed.")

if run_demo:
    res = pipeline.run(include_demo=True, include_live_rss=False)
    st.success(f"DEMO pipeline: ingested={res.ingested} stored={res.stored} deduped={res.deduped_dropped}")
    st.rerun()
if run_live:
    res = pipeline.run(include_demo=False, include_live_rss=True)
    st.success(
        f"Live RSS attempt: ingested={res.ingested} stored={res.stored} "
        f"(0 ingested is OK offline / blocked feeds)"
    )
    if res.errors:
        st.warning("; ".join(res.errors))
    st.rerun()

if repo.count_events() == 0:
    pipeline.seed_demo_if_empty()

demo_count = repo.count_events(is_demo=True)
live_count = repo.count_events(is_demo=False)
c1, c2, c3 = st.columns(3)
with c1:
    data_mode_chip(live_count > 0 and demo_count == 0)
    st.caption(f"Live events: {live_count}")
with c2:
    status_badge(f"DEMO {demo_count}", "warn" if demo_count else "info")
with c3:
    runs = repo.list_runs(limit=1)
    if runs:
        st.caption(f"Last run: {runs[0].get('status')} · stored={runs[0].get('docs_stored')}")


def _relative_time(iso: str) -> str:
    if not iso:
        return "Unknown time"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        sec = int((now - dt).total_seconds())
        if sec < 0:
            return "just now"
        if sec < 60:
            return f"{sec}s ago"
        if sec < 3600:
            return f"{sec // 60}m ago"
        if sec < 86400:
            return f"{sec // 3600}h ago"
        return f"{sec // 86400}d ago"
    except Exception:
        return iso[:19]


def _band_kind(band: str) -> str:
    return {"CRITICAL": "danger", "HIGH": "warn", "MEDIUM": "info", "LOW": "info"}.get(band, "info")


def _conf_kind(conf: str) -> str:
    return {
        "VERIFIED": "success",
        "HIGH": "success",
        "MEDIUM": "info",
        "LOW": "warn",
        "UNCONFIRMED": "warn",
    }.get((conf or "").upper(), "info")


def render_event_card(ev, key_prefix: str) -> None:
    band = ev.importance_band
    demo_label = " · DEMO / SYNTHETIC" if ev.is_demo or ev.status == EventStatus.DEMO.value else ""
    with st.container(border=True):
        top = st.columns([2, 1, 1, 1])
        with top[0]:
            status_badge(CATEGORY_LABELS.get(ev.category, ev.category), "info")
            if ev.is_demo:
                status_badge("DEMO", "warn")
        with top[1]:
            st.caption(_relative_time(ev.published_at or ev.discovered_at))
        with top[2]:
            status_badge(ev.confidence, _conf_kind(ev.confidence))
        with top[3]:
            status_badge(f"{band} {ev.importance}", _band_kind(band))

        st.markdown(f"**{ev.title}**")
        st.caption(f"Project: {ev.project} · Source: {ev.source}{demo_label}")
        st.write(ev.summary or ev.what_happened)

        with st.expander("Structured detail", expanded=False):
            st.markdown(f"**WHAT HAPPENED**  \n{ev.what_happened or ev.summary or 'Unknown'}")
            st.markdown(f"**WHY IT MATTERS**  \n{ev.why_it_matters or 'Informational research signal only.'}")
            st.markdown(f"**PROJECT**  \n{ev.project}")
            st.markdown(f"**CATEGORY**  \n{CATEGORY_LABELS.get(ev.category, ev.category)}")
            st.markdown(f"**SOURCE**  \n{ev.source} · `{ev.source_type}` · tier {ev.source_tier}")
            st.markdown(f"**CONFIDENCE**  \n{ev.confidence}")
            st.markdown(
                f"**PROVENANCE**  \n"
                f"published_at: `{ev.published_at or 'Unknown'}` · "
                f"discovered_at: `{ev.discovered_at or 'Unknown'}` · "
                f"discovery_latency_s: `{ev.discovery_latency_seconds if ev.discovery_latency_seconds is not None else 'Unknown'}`"
            )
            if ev.source_url:
                st.markdown(f"**source_url**  \n`{ev.source_url}`")
            else:
                st.caption("No source_url (Unknown) — will not invent a link.")

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if ev.source_url and ev.source_url.startswith("http"):
                st.link_button("Read Source", ev.source_url, use_container_width=True)
            else:
                st.button("Read Source", disabled=True, key=f"{key_prefix}_rs_{ev.id}", use_container_width=True)
        with b2:
            if st.button("Save/Bookmark", key=f"{key_prefix}_bm_{ev.id}", use_container_width=True):
                set_favourite("intelligence_event", ev.id, favourite=True, notes=ev.title[:200])
                st.toast("Bookmarked intelligence event")
        with b3:
            if st.button("Add to Project", key=f"{key_prefix}_ap_{ev.id}", use_container_width=True):
                name = ev.project if ev.project and ev.project != "Unknown" else ev.title[:80]
                if ev.is_demo and not str(name).upper().startswith("DEMO"):
                    name = f"DEMO: {name}"
                pid = add_project(
                    name=name,
                    chain=ev.blockchain if ev.blockchain != "Unknown" else "",
                    status="discovered",
                    notes=f"From Intelligence Center · event {ev.id}\n{ev.summary}",
                    priority=2,
                )
                st.toast(f"Added project #{pid} (DISCOVERED)")
        with b4:
            if st.button("Ignore", key=f"{key_prefix}_ig_{ev.id}", use_container_width=True):
                repo.set_event_status(ev.id, EventStatus.IGNORED.value)
                st.rerun()


st.page_link("pages/25_RWA_Intelligence.py", label="Open RWA — Real-World Assets Intelligence", icon="🏛️")

SECTION_SPECS = [
    ("Breaking", EventCategory.BREAKING.value),
    ("New Projects", EventCategory.NEW_PROJECTS.value),
    ("Funding", EventCategory.FUNDING.value),
    ("Airdrop Signals", EventCategory.AIRDROP_SIGNALS.value),
    ("Token Events", EventCategory.TOKEN_EVENTS.value),
    ("RWA — Real-World Assets", EventCategory.RWA.value),
]
for title, cat in SECTION_SPECS:
    section_header(title, "Sourced events · ranked by importance")
    events = repo.list_events(category=cat, limit=8)
    if not events:
        empty_state("No events in this section yet", "Run DEMO seed or live RSS from the expander above.")
    else:
        for ev in events:
            render_event_card(ev, key_prefix=f"{cat}")

section_header("Trending Narratives", "Theme clusters — DEMO labelled when synthetic")
narratives = repo.list_narratives(limit=10)
if not narratives:
    empty_state("No narratives yet", "DEMO narratives seed on first DEMO pipeline run.")
else:
    for n in narratives:
        with st.container(border=True):
            if n.get("is_demo"):
                status_badge("DEMO", "warn")
            st.markdown(f"**{n.get('title')}**")
            st.write(n.get("summary") or "")
            st.caption(f"slug: {n.get('slug')} · heat: {n.get('heat')}")

section_header("Watchlist", "Intelligence follows stub — wires to intelligence_watchlist")
watch = repo.list_watch(user_id=uid, limit=20)
if not watch:
    empty_state(
        "Watchlist is a stub in Phase 1",
        "Use Save/Bookmark on an event, or later follow projects/narratives. "
        "Market token watchlist remains under Watchlist page.",
    )
else:
    for w in watch:
        st.write(f"{w.get('ref_type')}: `{w.get('ref_id')}` — {w.get('notes') or ''}")

hi = repo.list_events(limit=5, min_importance=50)
if hi:
    with st.expander("Add top signal to intelligence watchlist"):
        labels = {f"{e.title[:60]} ({e.id[:8]})": e.id for e in hi}
        pick = st.selectbox("Event", list(labels.keys()))
        if st.button("Add to intel watchlist"):
            repo.add_watch("event", labels[pick], user_id=uid, notes="Phase1 stub follow")
            st.success("Added")
            st.rerun()

footer("Intelligence Center · Reports + Agent feed · engine is not a chatbot")
