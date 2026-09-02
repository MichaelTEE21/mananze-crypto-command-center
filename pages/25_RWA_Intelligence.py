"""MCCC RWA Intelligence Center — Real-World Assets research vertical."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.bookmarks import set_favourite
from mccc.db import init_db
from mccc.intelligence import IntelligencePipeline, IntelligenceRepository
from mccc.intelligence.rwa import (
    RWA_DISCLAIMER,
    RWAService,
    TOP_LEVEL_CATEGORY,
    VerificationStatus,
    all_rwa_categories,
    all_rwa_event_types,
)
from mccc.intelligence.rwa.taxonomy import (
    RWA_UI_SECTIONS,
    AssetValueType,
    category_label,
)
from mccc.intelligence.schema import EventCategory, EventStatus
from mccc.ui import (
    data_mode_chip,
    demo_callout,
    empty_state,
    footer,
    hero,
    metric_card,
    page_setup,
    section_header,
    session_user_id,
    status_badge,
)

page_setup("rwa_intelligence", "RWA Intelligence")
hero(
    TOP_LEVEL_CATEGORY,
    "Disclosure-based research signals · not financial advice · not trading/custody",
)
st.page_link("pages/24_Intelligence_Center.py", label="Intelligence Report · Analyse RWA entity", icon="🛰️")
st.caption("RWA vertical preserved — use entity type RWA in Intelligence Center Analyse.")

init_db()
uid = session_user_id()
rwa = RWAService()
rwa.ensure_ready()
rwa.seed_demo_if_empty()
repo = IntelligenceRepository()
pipeline = IntelligencePipeline()
pipeline.ensure_ready()

st.info(RWA_DISCLAIMER)
demo_callout(
    "DEMO / SYNTHETIC RWA rows are always labelled. Live ingestion is optional and cached — "
    "pages never fetch external sources on every load."
)

with st.expander("Seed / refresh (cached ingestion)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Refresh DEMO RWA seed", use_container_width=True):
            res = rwa.seed_demo(force=False)
            pipe = pipeline.run(include_demo=True, include_live_rss=False)
            st.success(
                f"Profiles stored={res.profiles_stored} skipped={res.skipped_existing} · "
                f"Events stored={pipe.stored}"
            )
            st.rerun()
    with c2:
        if st.button("Try live RSS (soft-fail)", use_container_width=True):
            pipe = pipeline.run(include_demo=False, include_live_rss=True)
            st.success(f"Live attempt stored={pipe.stored} (0 OK offline)")
            st.rerun()
    with c3:
        st.caption("Results cached in SQLite · repository ready for production DB swap.")

analytics = rwa.analytics()
m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card(str(analytics["total"]), "RWA profiles")
with m2:
    metric_card(str(analytics["demo"]), "DEMO / SYNTHETIC")
with m3:
    metric_card(str(analytics["live"]), "Live (non-demo)")
with m4:
    data_mode_chip(analytics["data_mode"] == "LIVE")
    st.caption(f"Mode: {analytics['data_mode']}")

if analytics["demo"]:
    status_badge("DEMO SEEDS ACTIVE", "warn")

# --- Filters ---
section_header("Filters", "Category · chain · verification · confidence · query")
cats = all_rwa_categories()
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    cat_opts = ["(all)"] + sorted(cats.keys())
    f_cat = st.selectbox("Category", cat_opts, format_func=lambda k: cats.get(k, k) if k != "(all)" else "(all)")
with fc2:
    f_chain = st.text_input("Chain contains", "").strip()
with fc3:
    ver_opts = ["(all)"] + [s.value for s in VerificationStatus]
    f_ver = st.selectbox("Verification", ver_opts)
with fc4:
    conf_opts = ["(all)", "VERIFIED", "HIGH", "MEDIUM", "LOW", "UNCONFIRMED"]
    f_conf = st.selectbox("Confidence", conf_opts)
f_q = st.text_input("Search profiles", placeholder="treasury, DEMO, ethereum…").strip()

profiles = rwa.repo.list_profiles(
    category=None if f_cat == "(all)" else f_cat,
    blockchain=f_chain or None,
    verification_status=None if f_ver == "(all)" else f_ver,
    confidence=None if f_conf == "(all)" else f_conf,
    q=f_q or None,
    limit=100,
)
if f_chain:
    profiles = [p for p in profiles if f_chain.lower() in (p.blockchain or "").lower()]

# --- Dashboard analytics ---
section_header("RWA Dashboard", "From stored profiles only — no fabricated TVL")
if not profiles and analytics["total"] == 0:
    empty_state("No RWA profiles yet", "Run DEMO seed above.")
else:
    left, right = st.columns(2)
    with left:
        st.caption("By category (stored)")
        for k, v in sorted(analytics["by_category"].items(), key=lambda x: -x[1])[:12]:
            st.write(f"· **{category_label(k)}** — {v}")
    with right:
        st.caption("By verification")
        for k, v in sorted(analytics["by_verification"].items(), key=lambda x: -x[1]):
            st.write(f"· `{k}` — {v}")
        st.caption(
            f"Asset values present: {analytics['with_asset_value']} · "
            f"Stale timestamps: {analytics['stale_asset_values']}"
        )

# --- Section tabs ---
section_header("RWA Intelligence Feed", "Breaking · categories · funding · institutional · regulatory · trends")
tab_labels = [s[0] for s in RWA_UI_SECTIONS]
tabs = st.tabs(tab_labels)


def _relative_time(iso: str) -> str:
    if not iso:
        return "Unknown time"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        sec = int((datetime.now(timezone.utc) - dt).total_seconds())
        if sec < 0:
            return "just now"
        if sec < 3600:
            return f"{sec // 60}m ago"
        if sec < 86400:
            return f"{sec // 3600}h ago"
        return f"{sec // 86400}d ago"
    except Exception:
        return iso[:19]


def render_profile_card(p, key_prefix: str) -> None:
    av = p.asset_value()
    with st.container(border=True):
        top = st.columns([2, 1, 1, 1])
        with top[0]:
            status_badge(category_label(p.rwa_category) if p.rwa_category else "RWA", "info")
            if p.is_demo:
                status_badge("DEMO / SYNTHETIC", "warn")
        with top[1]:
            status_badge(p.verification_status, "info")
        with top[2]:
            status_badge(p.confidence, "warn" if p.confidence == "UNCONFIRMED" else "info")
        with top[3]:
            st.caption(_relative_time(p.last_checked_at or p.updated_at))

        title = p.project_name
        if p.is_demo and "DEMO" not in title.upper():
            title = f"[DEMO] {title}"
        st.markdown(f"**{title}** · `{p.ticker}`")
        st.caption(f"Chain: {p.blockchain} · Asset type: {p.asset_type}")
        st.write(p.description or "No description disclosed.")

        # Asset value honesty
        stale = " · STALE timestamp" if av.is_stale else ""
        st.caption(
            f"Tokenized asset value: **{av.display_label()}** · "
            f"{av.amount} {av.currency} · measured_at: `{av.measured_at or 'Unknown'}`{stale}"
        )
        if av.value_type == AssetValueType.CALCULATED_ESTIMATE.value:
            status_badge("NOT TVL", "warn")

        with st.expander("Disclosure / risk framework (not a rating)", expanded=False):
            if p.disclosures:
                for d in p.disclosures:
                    st.write(f"· `{d.field_key}` → **{d.status}** {('— ' + d.detail) if d.detail else ''}")
            else:
                st.caption("No disclosure rows yet — treat fields as UNKNOWN.")
            st.markdown(
                f"**Jurisdiction:** {p.jurisdiction}  \n"
                f"**Regulatory:** {p.regulatory_status}  \n"
                f"**Custody:** {p.custody_info}  \n"
                f"**Issuer:** {p.issuer_info}  \n"
                f"**Collateral:** {p.collateral_info}  \n"
                f"**Funding notes:** {p.funding_notes}"
            )
            if p.provenance:
                st.markdown("**Provenance**")
                for pr in p.provenance:
                    st.caption(
                        f"{pr.claim_key or 'claim'}: {pr.source} · {pr.provenance_tier} · "
                        f"{pr.confidence} · {pr.source_url or 'no url'}"
                    )

        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            st.button("VIEW", key=f"{key_prefix}_view_{p.id}", use_container_width=True)
        with b2:
            if p.website_url and p.website_url.startswith("http"):
                st.link_button("OPEN WEBSITE", p.website_url, use_container_width=True)
            else:
                st.button("OPEN WEBSITE", disabled=True, key=f"{key_prefix}_web_{p.id}", use_container_width=True)
        with b3:
            if p.docs_url and p.docs_url.startswith("http"):
                st.link_button("OPEN DOCS", p.docs_url, use_container_width=True)
            else:
                st.button("OPEN DOCS", disabled=True, key=f"{key_prefix}_docs_{p.id}", use_container_width=True)
        with b4:
            if st.button("WATCHLIST", key=f"{key_prefix}_wl_{p.id}", use_container_width=True):
                rwa.repo.add_watch("profile", p.id, user_id=uid, notes=p.project_name[:120])
                st.toast("Added to RWA watchlist")
        with b5:
            if st.button("ADD TO PROJECT", key=f"{key_prefix}_ap_{p.id}", use_container_width=True):
                pid = rwa.add_to_project_tracker(p)
                st.toast(f"Project #{pid} (DISCOVERED)")

        if st.button("VIEW INTELLIGENCE", key=f"{key_prefix}_vi_{p.id}", use_container_width=True):
            set_favourite("rwa_profile", p.id, favourite=True, notes=p.project_name[:200])
            st.info("Open Intelligence Center for linked RWA events (tag: rwa).")


def events_for_section(section_key: str, limit: int = 8):
    if section_key == "breaking":
        return repo.list_events(category=EventCategory.BREAKING.value, limit=limit)
    if section_key == "new_projects":
        # RWA new project events + profiles
        ev = [e for e in repo.list_events(category=EventCategory.RWA.value, limit=40)
              if (e.subcategory or "") and "new" in (e.title or "").lower() or True]
        return [e for e in repo.list_events(category=EventCategory.RWA.value, limit=limit)]
    if section_key == "funding":
        return repo.list_events(category=EventCategory.FUNDING.value, limit=limit)
    if section_key == "institutional_adoption":
        return [
            e for e in repo.list_events(category=EventCategory.RWA.value, limit=40)
            if "institutional" in (e.title + e.summary + e.subcategory).lower()
            or "INSTITUTIONAL" in (e.raw_text or "")
        ][:limit]
    if section_key == "regulatory":
        return [
            e for e in repo.list_events(category=EventCategory.RWA.value, limit=40)
            if "regulat" in (e.title + e.summary).lower() or e.subcategory == "compliance_identity_infrastructure"
        ][:limit]
    if section_key == "trends":
        return []
    # category filter on profiles
    return None


for tab, (title, key) in zip(tabs, RWA_UI_SECTIONS):
    with tab:
        if key == "trends":
            narr = analytics.get("narratives") or []
            if not narr:
                empty_state("No observed RWA narratives yet", "Narratives derive from stored categories only.")
            else:
                for n in narr:
                    with st.container(border=True):
                        if n.get("is_demo"):
                            status_badge("DEMO", "warn")
                        st.markdown(f"**{n.get('title')}**")
                        st.write(n.get("summary") or "")
                        st.caption(f"heat={n.get('heat')} · slug={n.get('slug')}")
            continue

        if key in ("breaking", "new_projects", "funding", "institutional_adoption", "regulatory"):
            events = events_for_section(key)
            if not events:
                empty_state(f"No events for {title}", "Run DEMO seed or wait for live ingestion.")
            else:
                for ev in events:
                    demo = " · DEMO / SYNTHETIC" if ev.is_demo or ev.status == EventStatus.DEMO.value else ""
                    with st.container(border=True):
                        if ev.is_demo:
                            status_badge("DEMO", "warn")
                        status_badge(ev.category, "info")
                        st.markdown(f"**{ev.title}**")
                        st.caption(f"{ev.project} · {ev.source}{demo}")
                        st.write(ev.summary or ev.what_happened)
                        if ev.source_url and ev.source_url.startswith("http"):
                            st.link_button("Read source", ev.source_url)
            # also show matching profiles for new_projects
            if key == "new_projects":
                st.divider()
                st.caption("RWA profiles (directory)")
                for p in profiles[:8]:
                    render_profile_card(p, key_prefix=f"np_{key}")
            continue

        # Category-specific profile lists
        subset = [p for p in profiles if p.rwa_category == key]
        if not subset:
            # fall back to all filtered if browsing category tab with global filters empty
            subset = rwa.repo.list_profiles(category=key, limit=20)
        if not subset:
            empty_state(f"No profiles in {title}", "DEMO seeds cover a subset of categories.")
        else:
            for p in subset:
                render_profile_card(p, key_prefix=f"sec_{key}")

# --- Filtered directory ---
section_header("RWA Project Directory", f"{len(profiles)} matching filter")
if not profiles:
    empty_state("No matches", "Relax filters or refresh DEMO seed.")
else:
    for p in profiles:
        render_profile_card(p, key_prefix="dir")

# --- Watchlist ---
section_header("RWA Watchlist", "Projects · categories · chains · narratives")
wc1, wc2 = st.columns(2)
with wc1:
    wtype = st.selectbox("Watch type", ["profile", "category", "chain", "narrative"])
with wc2:
    if wtype == "profile" and profiles:
        labels = {f"{p.project_name} ({p.id[:8]})": p.id for p in profiles[:30]}
        pick = st.selectbox("Profile", list(labels.keys()) if labels else ["—"])
        ref = labels.get(pick, "")
    elif wtype == "category":
        pick = st.selectbox("Category", sorted(cats.keys()), format_func=lambda k: cats[k])
        ref = pick
    elif wtype == "chain":
        ref = st.text_input("Chain id", "ethereum")
        pick = ref
    else:
        narr = analytics.get("narratives") or []
        opts = {n["title"]: n["slug"] for n in narr} or {"(none)": ""}
        pick = st.selectbox("Narrative", list(opts.keys()))
        ref = opts.get(pick, "")
if st.button("Add to RWA watchlist") and ref:
    rwa.repo.add_watch(wtype, ref, user_id=uid, notes=str(pick)[:120])
    st.success("Added")
    st.rerun()

watch = rwa.repo.list_watch(user_id=uid, limit=30)
if not watch:
    empty_state("Watchlist empty", "Follow profiles, categories, chains, or narratives.")
else:
    for w in watch:
        st.write(f"· `{w.get('ref_type')}` → **{w.get('ref_id')}** — {w.get('notes') or ''}")

# Education CTA
section_header("Education", "Tokenization · treasuries · credit · real estate · custody · risks")
st.page_link("pages/8_Education.py", label="Open Education (RWA modules)", icon="📚")
st.caption("Educational modules only — disclosure framework, not buy/sell advice.")

footer("RWA Intelligence Phase 1 · MCCC only · not Technocore")
