"""Shared premium dark UI helpers for Streamlit pages."""
from __future__ import annotations

import html
import os
from typing import Optional

import streamlit as st

from mccc import APP_NAME, APP_TAGLINE, __version__
from mccc.db import init_db, log_event

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --mccc-bg: #0a0e13;
  --mccc-panel: #121820;
  --mccc-panel-2: #0f141b;
  --mccc-border: #243040;
  --mccc-border-soft: #1e2a36;
  --mccc-text: #e8eef5;
  --mccc-muted: #9aa7b5;
  --mccc-accent: #00d4aa;
  --mccc-success: #3dffb5;
  --mccc-warn: #ffb020;
  --mccc-danger: #ff6b6b;
  --mccc-info: #5eb3ff;
  --mccc-pro: #c4a0ff;
}

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}

/* Dense terminal cards */
.mccc-hero {
  background: linear-gradient(135deg, #0b0f14 0%, #12202b 45%, #0d281f 100%);
  border: 1px solid var(--mccc-border-soft);
  border-radius: 12px;
  padding: 0.95rem 1.15rem;
  margin-bottom: 0.7rem;
  box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}
.mccc-hero h1 {
  margin: 0;
  font-size: 1.4rem;
  letter-spacing: 0.04em;
  color: var(--mccc-text);
}
.mccc-hero .tag {
  color: var(--mccc-accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  margin-top: 0.25rem;
}
.mccc-hero .sub {
  color: var(--mccc-muted);
  margin-top: 0.35rem;
  font-size: 0.85rem;
}

.mccc-section-header {
  margin: 0.55rem 0 0.45rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--mccc-border-soft);
}
.mccc-section-header h3 {
  margin: 0;
  font-size: 1.02rem;
  color: var(--mccc-text);
  letter-spacing: 0.03em;
}
.mccc-section-header .sub {
  color: var(--mccc-muted);
  font-size: 0.78rem;
  margin-top: 0.15rem;
}

.mccc-badge,
.mccc-badge-success,
.mccc-badge-warn,
.mccc-badge-danger,
.mccc-badge-info,
.mccc-badge-pro,
.mccc-badge-live,
.mccc-badge-demo {
  display: inline-block;
  padding: 0.1rem 0.48rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin-right: 0.22rem;
  vertical-align: middle;
  line-height: 1.35;
}
.mccc-badge {
  background: #1a2e28;
  color: var(--mccc-accent);
  border: 1px solid #00d4aa55;
}
.mccc-badge-success {
  background: #0f2a1c;
  color: var(--mccc-success);
  border: 1px solid #3dffb555;
}
.mccc-badge-warn {
  background: #2e241a;
  color: var(--mccc-warn);
  border: 1px solid #ffb02055;
}
.mccc-badge-danger {
  background: #2a1414;
  color: var(--mccc-danger);
  border: 1px solid #ff6b6b55;
}
.mccc-badge-info {
  background: #14202a;
  color: var(--mccc-info);
  border: 1px solid #5eb3ff55;
}
.mccc-badge-pro {
  background: #241a2e;
  color: var(--mccc-pro);
  border: 1px solid #c4a0ff55;
}
.mccc-badge-live {
  background: #0f2a1c;
  color: var(--mccc-success);
  border: 1px solid #3dffb555;
}
.mccc-badge-demo {
  background: #2a2210;
  color: #ffcc66;
  border: 1px solid #ffcc6655;
}

.mccc-chip-live, .mccc-chip-demo {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.18rem 0.65rem;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.08em;
}
.mccc-chip-live {
  background: #0f2a1c;
  color: var(--mccc-success);
  border: 1px solid #3dffb555;
}
.mccc-chip-demo {
  background: #2a2210;
  color: #ffcc66;
  border: 1px solid #ffcc6655;
}
.mccc-chip-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  display: inline-block;
}
.mccc-chip-live .mccc-chip-dot { background: var(--mccc-success); box-shadow: 0 0 6px #3dffb5aa; }
.mccc-chip-demo .mccc-chip-dot { background: #ffcc66; }

.mccc-card {
  background: var(--mccc-panel);
  border: 1px solid var(--mccc-border);
  border-radius: 9px;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.45rem;
}
.mccc-card-dense {
  background: var(--mccc-panel-2);
  border: 1px solid var(--mccc-border-soft);
  border-radius: 8px;
  padding: 0.55rem 0.7rem;
  margin-bottom: 0.4rem;
}
.mccc-metric {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.15rem;
  color: var(--mccc-accent);
  line-height: 1.15;
}
.mccc-metric-label {
  color: var(--mccc-muted);
  font-size: 0.74rem;
  margin-top: 0.15rem;
}
.mccc-metric-delta-up { color: var(--mccc-success); font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; }
.mccc-metric-delta-down { color: var(--mccc-danger); font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; }
.mccc-metric-delta-flat { color: var(--mccc-muted); font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; }

.mccc-empty {
  background: #10161e;
  border: 1px dashed #2a3848;
  border-radius: 9px;
  padding: 0.95rem 1.05rem;
  text-align: center;
  color: var(--mccc-muted);
  margin: 0.4rem 0 0.6rem;
}
.mccc-empty strong { color: var(--mccc-text); display: block; margin-bottom: 0.3rem; }

.mccc-error {
  background: #2a1414;
  border: 1px solid #5a2020;
  border-radius: 9px;
  padding: 0.65rem 0.9rem;
  color: #ffb0b0;
  margin: 0.35rem 0 0.55rem;
  font-size: 0.88rem;
}

.mccc-kanban {
  background: #10161e;
  border: 1px solid var(--mccc-border);
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  margin-bottom: 0.4rem;
  min-height: 2.9rem;
}
.mccc-kanban .title { color: var(--mccc-text); font-weight: 600; font-size: 0.85rem; }
.mccc-kanban .meta { color: #8a97a6; font-size: 0.72rem; margin-top: 0.15rem; }

.mccc-list-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid #1a2430;
  font-size: 0.85rem;
}
.mccc-list-row:last-child { border-bottom: none; }
.mccc-list-row .title { color: var(--mccc-text); font-weight: 500; }
.mccc-list-row .meta { color: var(--mccc-muted); font-size: 0.75rem; white-space: nowrap; }

.mccc-footer {
  margin-top: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--mccc-border-soft);
  color: var(--mccc-muted);
  font-size: 0.75rem;
}
.mccc-footer .ver {
  font-family: 'JetBrains Mono', monospace;
  color: var(--mccc-accent);
}

.mccc-quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.35rem 0 0.55rem;
}

/* Tables */
div[data-testid="stDataFrame"] {
  border: 1px solid var(--mccc-border-soft);
  border-radius: 8px;
  overflow: hidden;
}
div[data-testid="stDataFrame"] table {
  font-size: 0.82rem;
}
div[data-testid="stDataFrame"] th {
  background: #0f141b !important;
  color: var(--mccc-muted) !important;
  font-weight: 600 !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.7rem !important;
}

/* Sidebar polish */
div[data-testid="stSidebar"] {
  background: var(--mccc-bg);
  border-right: 1px solid var(--mccc-border-soft);
}
div[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  font-size: 0.85rem;
}
div[data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace;
}

/* Mobile-friendly tweaks */
@media (max-width: 768px) {
  .mccc-hero { padding: 0.8rem 0.9rem; border-radius: 10px; }
  .mccc-hero h1 { font-size: 1.2rem; }
  .mccc-card, .mccc-card-dense { padding: 0.55rem 0.65rem; }
  .mccc-metric { font-size: 1.02rem; }
  .mccc-list-row { flex-direction: column; gap: 0.15rem; }
  .mccc-footer { font-size: 0.7rem; }
}
</style>
"""

_STATUS_CLASS = {
    "success": "mccc-badge-success",
    "ok": "mccc-badge-success",
    "warn": "mccc-badge-warn",
    "warning": "mccc-badge-warn",
    "danger": "mccc-badge-danger",
    "error": "mccc-badge-danger",
    "info": "mccc-badge-info",
    "pro": "mccc-badge-pro",
    "live": "mccc-badge-live",
    "demo": "mccc-badge-demo",
    "default": "mccc-badge",
}


def inject_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _pro_unlocked() -> bool:
    if os.environ.get("MCCC_PRO_UNLOCK", "0") == "1":
        return True
    try:
        from mccc.subscriptions import is_pro
        from mccc.auth import get_session_user

        user = get_session_user()
        uid = user.get("id") if user else None
        return is_pro(user_id=uid)
    except Exception:
        return False


def page_setup(page_key: str, title: str, icon: str = "◆") -> None:
    st.set_page_config(
        page_title=f"{title} · MCCC",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_db()
    # Light config validation (warn once per session) + admin bootstrap
    try:
        from mccc.config import validate_config
        from mccc.auth import maybe_bootstrap_admin

        maybe_bootstrap_admin()
        if not st.session_state.get("_mccc_config_checked"):
            warns = validate_config()
            st.session_state["_mccc_config_checked"] = True
            st.session_state["_mccc_config_warnings"] = warns
    except Exception:
        pass
    inject_css()
    try:
        log_event("page_view", page_key=page_key)
    except Exception:
        pass

    unread = 0
    try:
        from mccc.notifications import unread_count
        from mccc.auth import get_session_user

        user = get_session_user()
        uid = user.get("id") if user else None
        unread = unread_count(user_id=uid)
    except Exception:
        unread = 0

    with st.sidebar:
        st.markdown(f"**{APP_NAME}**")
        st.caption(f"{APP_TAGLINE}")
        st.caption(f"v{__version__}")
        badges = ['<span class="mccc-badge">LOCAL · PRIVACY-FIRST</span>']
        if _pro_unlocked():
            badges.append('<span class="mccc-badge-pro">PRO</span>')
        st.markdown(" ".join(badges), unsafe_allow_html=True)
        if unread:
            st.markdown(
                f'<span class="mccc-badge-warn">🔔 {unread} unread</span>',
                unsafe_allow_html=True,
            )
        try:
            from mccc.auth import get_session_user

            user = get_session_user()
            if user:
                st.caption(f"Signed in · {user.get('display_name') or user.get('email')}")
            else:
                st.caption("Guest · local single-user mode")
        except Exception:
            pass
        st.divider()
        render_sidebar_nav()
        st.divider()
        st.caption("B=MananzeZA · never stores seeds / private keys")


def render_sidebar_nav() -> None:
    """Structured nav — reuses existing pages; Phase N placeholders labelled."""
    st.caption("Navigate")
    st.page_link("app.py", label="Command Center", icon="🏠")
    st.page_link("pages/18_Search.py", label="Search", icon="🔍")
    st.page_link("pages/24_Intelligence_Center.py", label="Intelligence", icon="🛰️")
    st.page_link("pages/3_Airdrop_Tracker.py", label="Airdrops", icon="🪂")
    st.page_link("pages/26_Tokens.py", label="Tokens", icon="🪙")
    st.page_link("pages/4_Wallet_Tracking.py", label="Wallets", icon="👀")
    st.page_link("pages/27_Calendar.py", label="Calendar", icon="📅")
    st.page_link("pages/2_Project_Tracker.py", label="Projects", icon="📁")
    st.page_link("pages/6_Analytics.py", label="Analytics", icon="📊")
    st.page_link("pages/25_RWA_Intelligence.py", label="RWA", icon="🏛️")
    st.page_link("pages/8_Education.py", label="Learn", icon="📚")
    st.page_link("pages/7_AI_Assistant.py", label="Agent", icon="🤖")
    st.page_link("pages/15_Notifications.py", label="Alerts", icon="🔔")
    st.page_link("pages/21_Research.py", label="My Research", icon="📝")
    with st.expander("Coming later (roadmap)", expanded=False):
        st.caption("Whales — Phase 2/3 · Protocols / Ecosystems deep intel — Phase 4 · Live feed polish — Phase 5")
        st.page_link("pages/20_Exchange_Directory.py", label="Protocols (exchanges dir · interim)", icon="🏦")
        st.page_link("pages/14_Watchlist.py", label="Watchlist / alert rules", icon="⭐")


def hero(title: str, subtitle: str = "", show_demo_banner: bool = False) -> None:
    from mccc.demo_data import DEMO_BANNER

    demo_html = ""
    if show_demo_banner:
        demo_html = f'<div class="tag">{html.escape(DEMO_BANNER)}</div>'
    st.markdown(
        f"""
        <div class="mccc-hero">
          <span class="mccc-badge">MCCC</span>
          <h1>{html.escape(title)}</h1>
          <div class="sub">{html.escape(subtitle)}</div>
          {demo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge_html(text: str, kind: str = "info") -> str:
    """Pure HTML for a status badge (testable without Streamlit)."""
    cls = _STATUS_CLASS.get((kind or "info").lower(), "mccc-badge-info")
    return f'<span class="{cls}">{html.escape(str(text))}</span>'


def status_badge(text: str, kind: str = "info") -> None:
    st.markdown(status_badge_html(text, kind), unsafe_allow_html=True)


def data_mode_chip_html(is_live: bool) -> str:
    """Pure HTML LIVE/DEMO environment chip."""
    if is_live:
        return (
            '<span class="mccc-chip-live">'
            '<span class="mccc-chip-dot"></span>LIVE</span>'
        )
    return (
        '<span class="mccc-chip-demo">'
        '<span class="mccc-chip-dot"></span>DEMO</span>'
    )


def data_mode_chip(is_live: bool) -> None:
    """Render LIVE/DEMO environment chip (honest labelling)."""
    st.markdown(data_mode_chip_html(is_live), unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "") -> None:
    sub = f'<div class="sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="mccc-section-header"><h3>{html.escape(title)}</h3>{sub}</div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, hint: str = "") -> None:
    hint_html = f"<div>{html.escape(hint)}</div>" if hint else ""
    st.markdown(
        f'<div class="mccc-empty"><strong>{html.escape(title)}</strong>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def error_banner(msg: str) -> None:
    st.markdown(
        f'<div class="mccc-error">{html.escape(msg)}</div>',
        unsafe_allow_html=True,
    )


def loading(caption: str = "Loading…") -> None:
    st.caption(f"⏳ {caption}")


def live_or_demo_badge(is_live: bool) -> None:
    """Back-compat alias — prefer data_mode_chip for cockpit UI."""
    data_mode_chip(is_live)


def demo_callout(text: str | None = None) -> None:
    from mccc.demo_data import DEMO_BANNER

    st.warning(text or DEMO_BANNER)


def pro_locked_panel(feature_name: str) -> None:
    st.markdown(
        f"""
        <div class="mccc-card">
          <span class="mccc-badge-pro">PRO ARCHITECTURE</span>
          <p style="margin-top:0.55rem;color:#cfd8e3;"><strong>{html.escape(feature_name)}</strong> is gated.
          Stripe checkout is <em>Coming Soon</em> ($4/mo planned). No payment is processed.
          Toggle flags in <em>PRO Architecture</em> or set <code>MCCC_PRO_UNLOCK=1</code> locally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def upgrade_cta(reason: str = "") -> None:
    """Soft-gate upgrade call-to-action — never claims payment succeeded."""
    from mccc.subscriptions import PRO_PAYMENTS_MESSAGE, PRO_PRICE_LABEL, upgrade_cta_markdown

    extra = f"<p style=\"color:#9aa7b5;\">{html.escape(reason)}</p>" if reason else ""
    st.markdown(
        f"""
        <div class="mccc-card">
          <span class="mccc-badge-pro">UPGRADE · {html.escape(PRO_PRICE_LABEL)}</span>
          {extra}
          <p style="margin-top:0.45rem;color:#cfd8e3;">{html.escape(PRO_PAYMENTS_MESSAGE)}
          Stripe checkout is Coming Soon — no card capture, no fake success.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/10_PRO_Architecture.py", label="Open PRO Architecture", icon="⭐")
    st.caption(upgrade_cta_markdown())


def affiliate_disclosure() -> None:
    """Required wherever partner / referral links appear."""
    from mccc.partners import AFFILIATE_DISCLOSURE

    st.info(AFFILIATE_DISCLOSURE)


def affiliate_disclosure_short() -> None:
    st.caption(
        "Some links may be partner/referral links; MCCC may receive compensation at no extra cost to you."
    )


def seed_phrase_warning() -> None:
    """Surface the never-ask-seed / private-key warning."""
    from mccc.partners import SEED_PHRASE_WARNING

    st.warning(SEED_PHRASE_WARNING)


def metric_card(
    value: str,
    label: str,
    *,
    delta: Optional[str] = None,
    delta_kind: str = "flat",
    use_st_metric: bool = False,
) -> None:
    """Dense HTML metric card, or optional st.metric wrapper."""
    if use_st_metric:
        st.metric(label, value, delta=delta)
        return
    delta_html = ""
    if delta is not None:
        dcls = {
            "up": "mccc-metric-delta-up",
            "down": "mccc-metric-delta-down",
            "success": "mccc-metric-delta-up",
            "danger": "mccc-metric-delta-down",
            "flat": "mccc-metric-delta-flat",
        }.get((delta_kind or "flat").lower(), "mccc-metric-delta-flat")
        delta_html = f'<div class="{dcls}">{html.escape(str(delta))}</div>'
    st.markdown(
        f'<div class="mccc-card"><div class="mccc-metric">{html.escape(str(value))}</div>'
        f'{delta_html}'
        f'<div class="mccc-metric-label">{html.escape(str(label))}</div></div>',
        unsafe_allow_html=True,
    )


def footer(extra: str = "") -> None:
    """Page footer with package version."""
    extra_html = f" · {html.escape(extra)}" if extra else ""
    st.markdown(
        f'<div class="mccc-footer">'
        f'<span class="ver">MCCC v{html.escape(__version__)}</span>'
        f"{extra_html}"
        f" · local · privacy-first · not financial advice"
        f"</div>",
        unsafe_allow_html=True,
    )


def quick_actions() -> None:
    """Hub quick links to key multipage destinations."""
    cols = st.columns(4)
    with cols[0]:
        st.page_link("pages/18_Search.py", label="Search", icon="🔍")
        st.page_link("pages/24_Intelligence_Center.py", label="Intelligence", icon="🛰️")
    with cols[1]:
        st.page_link("pages/4_Wallet_Tracking.py", label="Wallets", icon="👀")
        st.page_link("pages/26_Tokens.py", label="Tokens", icon="🪙")
    with cols[2]:
        st.page_link("pages/27_Calendar.py", label="Calendar", icon="📅")
        st.page_link("pages/3_Airdrop_Tracker.py", label="Airdrops", icon="🪂")
    with cols[3]:
        st.page_link("pages/2_Project_Tracker.py", label="Projects", icon="📁")
        st.page_link("pages/25_RWA_Intelligence.py", label="RWA", icon="🏛️")
        st.page_link("pages/8_Education.py", label="Learn", icon="📚")


def session_user_id():
    try:
        from mccc.auth import get_session_user

        user = get_session_user()
        return user.get("id") if user else None
    except Exception:
        return None


def partner_cta(link: dict, key_prefix: str = "partner", source_page: str = "") -> None:
    """Render CTA: Track & open records a click, then primary link_button to resolved URL."""
    from mccc.partners import cta_label, record_click, resolve_visit_url

    url = resolve_visit_url(link)
    label = cta_label(link.get("category", "Partner"))
    is_ref = bool((link.get("referral_url") or "").strip())
    dest_note = "Partner / referral destination" if is_ref else "Official website"
    lid = link["id"]
    open_key = f"{key_prefix}_open_{lid}"
    track_key = f"{key_prefix}_track_{lid}"

    st.caption(f"Outbound: **{dest_note}** · `{url}`")
    col_a, col_b = st.columns((1, 1))
    with col_a:
        if st.button("Track & open", key=track_key, use_container_width=True):
            try:
                record_click(lid, source_page=source_page or key_prefix)
                st.session_state[open_key] = url
                st.success("Visit logged (no IP / fingerprint stored).")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not log visit: {exc}")
    with col_b:
        st.link_button(label, url, use_container_width=True)
    if st.session_state.get(open_key):
        st.link_button("Open now", st.session_state[open_key], type="primary", use_container_width=True)
