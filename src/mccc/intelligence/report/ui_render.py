"""Streamlit render helpers for Intelligence Reports (no page_setup)."""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from mccc.intelligence.report.education import journey_steps, mode_copy, render_explainer_markdown
from mccc.intelligence.report.schema import REPORT_DISCLAIMER, IntelligenceReport
from mccc.ui import data_mode_chip, empty_state, section_header, status_badge


def render_journey_strip() -> None:
    steps = journey_steps()
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            st.markdown(f"**{i+1}. {step['step']}**")
            st.caption(step["detail"])


def render_security_block() -> None:
    st.error(
        "PUBLIC ADDRESS ONLY — never paste seed phrases, private keys, wallet passwords, "
        "or recovery phrases. MCCC does not need control of your wallet to analyse public blockchain activity."
    )


def render_report(report: IntelligenceReport, *, beginner_mode: bool = True) -> None:
    mode = mode_copy(beginner_mode)
    st.caption(f"{mode['label']}: {mode['blurb']}")
    st.info(REPORT_DISCLAIMER)

    # Header chips
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        status_badge(report.entity_type.upper(), "info")
        if report.is_demo or report.data_mode == "DEMO":
            status_badge("DEMO / SYNTHETIC", "demo")
    with c2:
        live = report.data_mode == "LIVE"
        data_mode_chip(live)
        st.caption(report.data_mode)
    with c3:
        kind = {"HIGH": "success", "MEDIUM": "info", "LOW": "warn"}.get(report.confidence, "info")
        status_badge(f"CONFIDENCE {report.confidence}", kind)
    with c4:
        st.caption(f"Report `{report.report_id[:8]}…` · {report.created_at}")

    if report.unsupported_reason or report.entity_type in ("unsupported", "unknown"):
        st.error(report.executive_summary or report.unsupported_reason)
        return

    for w in report.warnings:
        st.warning(w)
    for e in report.errors:
        st.error(e)

    section_header("1 · Executive summary", "Beginner-friendly · no buy/sell")
    st.markdown(report.executive_summary)

    section_header("2 · What is this?", "Plain language + Advanced View")
    st.markdown(report.what_is_this_plain)
    if not beginner_mode:
        with st.expander("Advanced View", expanded=True):
            st.code(report.what_is_this_advanced or "", language="text")
    else:
        with st.expander("Advanced View", expanded=False):
            st.code(report.what_is_this_advanced or "", language="text")

    section_header("3 · On-chain activity", "Only where reliable · every metric sourced")
    if not report.on_chain_metrics:
        empty_state("No on-chain metrics", "DATA UNAVAILABLE or not applicable for this entity.")
    else:
        for m in report.on_chain_metrics:
            with st.container(border=True):
                if m.unavailable_reason or m.value is None:
                    st.markdown(f"**{m.label}:** DATA UNAVAILABLE")
                    st.caption(m.unavailable_reason or "Insufficient data")
                else:
                    unit = f" {m.unit}" if m.unit else ""
                    st.markdown(f"**{m.label}:** `{m.value}`{unit}")
                if m.provenance:
                    live_tag = "LIVE" if m.provenance.is_live else "not live"
                    st.caption(
                        f"source={m.provenance.source} · ts={m.provenance.timestamp} · "
                        f"chain={m.provenance.chain} · {live_tag} · "
                        f"verification={m.provenance.verification}"
                    )
                    st.caption(m.provenance.definition)
                if not beginner_mode:
                    with st.expander(f"Metric explainer · {m.key}", expanded=False):
                        st.markdown(render_explainer_markdown(m.key))

    section_header("4 · Wallet / address intelligence", "Public only")
    wi = report.wallet_intelligence or {}
    if not wi:
        st.caption("Not applicable (or no address intelligence for this entity type).")
    else:
        st.markdown(wi.get("interaction_note") or "Public address research note.")
        st.caption(
            f"address=`{wi.get('address')}` · chain=`{wi.get('chain')}` · "
            f"status=`{wi.get('data_status')}` · balances={wi.get('balance_count')}"
        )
        if wi.get("total_known_usd") is not None:
            st.caption(f"Sum of known USD labels (may be DEMO): {wi.get('total_known_usd')}")

    section_header("5 · Token intelligence", "Verified vs estimated vs user-provided")
    ti = report.token_intelligence or {}
    if not ti:
        st.caption("Not applicable for this entity type.")
    else:
        st.markdown(
            f"**{ti.get('name') or 'Unknown'}** (`{ti.get('symbol') or '?'}`) · "
            f"verification=`{ti.get('verification')}`"
        )
        st.caption(ti.get("verification_note") or "")
        live = "LIVE" if ti.get("is_live") else "DEMO/FALLBACK"
        st.caption(f"mode={live} · token_id={ti.get('token_id')}")

    section_header("6 · Risk / red flags", "Neutral research language only")
    if not report.risk_flags:
        empty_state("No flags raised", "Absence of flags is not a safety rating — No conclusion.")
    else:
        for rf in report.risk_flags:
            kind = {"warn": "warn", "investigate": "danger", "info": "info"}.get(rf.severity, "info")
            status_badge(rf.language, kind)
            st.markdown(f"**{rf.title}** — {rf.detail}")

    section_header("7 · What changed?", "Vs prior observations — no invented causes")
    if not report.changes:
        st.caption("No prior observation for this entity key, or no differences detected.")
    else:
        for ch in report.changes:
            st.markdown(
                f"- **{ch.field}**: `{ch.previous}` → `{ch.current}` "
                f"({ch.observed_at_previous or '?'} → {ch.observed_at_current or '?'})"
            )
            st.caption(ch.note)

    section_header("8 · Beginner explanation", "What / why / next")
    if report.beginner:
        st.markdown(f"**What does this mean?**  \n{report.beginner.what_does_this_mean}")
        st.markdown(f"**Why should I care?**  \n{report.beginner.why_should_i_care}")
        st.markdown(f"**What to investigate next?**  \n{report.beginner.what_to_investigate_next}")
    else:
        st.caption("Beginner block unavailable.")

    section_header("9 · Sources", "Real only — no fabricated links")
    for s in report.sources:
        line = f"**{s.title}** · `{s.source_type}`"
        if s.note:
            line += f" — {s.note}"
        st.markdown(line)
        if s.url and s.url.startswith("http"):
            st.caption(s.url)

    section_header("10 · Confidence / data quality", "HIGH / MEDIUM / LOW with reasons")
    status_badge(report.confidence, {"HIGH": "success", "MEDIUM": "info", "LOW": "warn"}.get(report.confidence, "info"))
    for r in report.confidence_reasons:
        st.markdown(f"- {r}")

    # Stash for AI assistant
    st.session_state["mccc_current_report"] = report.to_dict()
    st.session_state["mccc_current_report_context"] = report.context_for_assistant()
