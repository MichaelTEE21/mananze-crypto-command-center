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


def _load_css() -> str:
    """Design-system CSS (premium terminal). Fallback kept minimal if import fails."""
    try:
        from mccc.design_system import build_css

        return build_css()
    except Exception:
        return "<style>body{background:#070b10;color:#e8eef5;}</style>"


CUSTOM_CSS = None  # resolved at inject time via _load_css()

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
    st.markdown(_load_css(), unsafe_allow_html=True)


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




def render_support_cta_banner(compact: bool = False) -> None:
    """Always-accessible, unobtrusive Support CTA (not a blocking modal)."""
    if compact:
        st.caption("Support MCCC · voluntary public donations")
        st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon="💜")
        return
    st.markdown(
        '<div class="mccc-card" style="margin:0.35rem 0 0.55rem;">'
        '<span class="mccc-badge">SUPPORT</span>'
        '<p style="margin:0.4rem 0 0.25rem;color:#cfd8e3;font-size:0.9rem;">'
        'MCCC stays independent through voluntary public donations (BTC / ETH / SOL). '
        'Never a PRO purchase. Never share seeds or private keys.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/28_Support_MCCC.py", label="Open Support MCCC", icon="💜")


def maybe_show_support_soft_prompt(page_key: str) -> None:
    """First-visit delayed soft prompt on Command Center — easy dismiss, never every nav."""
    try:
        from mccc.auth import get_session_user
        from mccc.donations import (
            DONATION_WARNING,
            dismiss_donate_prompt,
            get_donation_channels,
            should_show_donate_soft_prompt,
        )

        user = None
        try:
            user = get_session_user()
        except Exception:
            user = None
        uid = user.get("id") if user else None
        if not should_show_donate_soft_prompt(page_key, user_id=uid):
            return

        # Mark shown so we don't re-open mid-session even before dismiss
        st.session_state["_mccc_donate_prompt_shown"] = True

        with st.expander("💜 Support MCCC — optional (first visit)", expanded=True):
            st.caption(
                "A quiet thank-you prompt after you have started exploring. "
                "Dismiss anytime — Support stays in the sidebar."
            )
            st.info(DONATION_WARNING)
            channels = get_donation_channels()
            cols = st.columns(min(3, len(channels) or 1))
            for col, ch in zip(cols, channels):
                with col:
                    st.markdown(f"**{ch.asset}** · {ch.network}")
                    st.code(ch.address, language=None)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.page_link("pages/28_Support_MCCC.py", label="Full Support page", icon="💜")
            with c2:
                if st.button("Maybe later", key="mccc_donate_soft_later", use_container_width=True):
                    dismiss_donate_prompt(user_id=uid, durable=False)
                    st.rerun()
            with c3:
                if st.button("Don't show again", type="primary", key="mccc_donate_soft_dismiss", use_container_width=True):
                    dismiss_donate_prompt(user_id=uid, durable=True)
                    st.rerun()
    except Exception:
        pass


# Back-compat alias (old aggressive modal name → soft prompt)
def maybe_show_support_modal(page_key: str) -> None:
    maybe_show_support_soft_prompt(page_key)


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
        st.markdown("**MCCC**")
        st.caption("Crypto intelligence terminal")
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
    """Experience-oriented nav — sparse icons; backends preserved."""
    from mccc.design_system import NAV_ICONS

    st.markdown('<div class="mccc-nav-group">Command</div>', unsafe_allow_html=True)
    st.page_link("app.py", label="Dashboard", icon=NAV_ICONS["dashboard"])
    st.page_link("pages/18_Search.py", label="Explore", icon=NAV_ICONS["explore"])
    st.page_link("pages/24_Intelligence_Center.py", label="Intelligence", icon="🛰️")
    st.page_link("pages/26_Tokens.py", label="Tokens", icon="🪙")

    st.markdown('<div class="mccc-nav-group">On-chain</div>', unsafe_allow_html=True)
    st.page_link("pages/4_Wallet_Tracking.py", label="Wallets", icon=NAV_ICONS["wallets"])
    st.page_link("pages/32_Chain_Explorers.py", label="On-chain", icon=NAV_ICONS["onchain"])
    st.page_link("pages/19_Wallet_Directory.py", label="Wallet Hub", icon="📒")
    st.page_link("pages/33_Crypto_Directory.py", label="Crypto Directory", icon="🗂️")

    st.markdown('<div class="mccc-nav-group">Research</div>', unsafe_allow_html=True)
    st.page_link("pages/6_Analytics.py", label="Analytics", icon=NAV_ICONS["analytics"])
    st.page_link("pages/1_Markets.py", label="Markets", icon="📈")
    st.page_link("pages/7_AI_Assistant.py", label="AI Analyst", icon=NAV_ICONS["analyst"])
    st.page_link("pages/2_Project_Tracker.py", label="Projects", icon=NAV_ICONS["projects"])
    st.page_link("pages/3_Airdrop_Tracker.py", label="Airdrops", icon="🪂")
    st.page_link("pages/14_Watchlist.py", label="Watchlist", icon=NAV_ICONS["watchlist"])
    st.page_link("pages/15_Notifications.py", label="Alerts", icon="🔔")
    st.page_link("pages/25_RWA_Intelligence.py", label="RWA", icon="🏛️")

    st.markdown('<div class="mccc-nav-group">Learn</div>', unsafe_allow_html=True)
    st.page_link("pages/8_Education.py", label="Academy", icon=NAV_ICONS["academy"])
    st.page_link("pages/17_Start_Here.py", label="Start Crypto", icon="🚀")
    st.page_link("pages/21_Research.py", label="My Research", icon="📝")

    st.markdown('<div class="mccc-nav-group">Account</div>', unsafe_allow_html=True)
    st.page_link("pages/16_Account.py", label="Account", icon="👤")
    st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon=NAV_ICONS["support"])
    st.page_link("pages/10_PRO_Architecture.py", label="PRO", icon="💎")

    with st.expander("More", expanded=False):
        st.page_link("pages/27_Calendar.py", label="Calendar", icon="📅")
        st.page_link("pages/20_Exchange_Directory.py", label="Exchange Hub", icon="🏦")
        st.page_link("pages/34_DEX_Hub.py", label="DEX Hub", icon="🔄")
        st.page_link("pages/11_Partner_Directory.py", label="Partners", icon="🤝")
        st.page_link("pages/35_Admin_Partner_Analytics.py", label="Partner Analytics", icon="📊")
        st.page_link("pages/5_Market_APIs.py", label="Market APIs", icon="🔌")
        st.page_link("pages/9_User_Analytics.py", label="Usage", icon="📉")
        st.page_link("pages/29_About.py", label="About", icon="ℹ️")
        st.page_link("pages/30_Privacy.py", label="Privacy", icon="🔒")
        st.page_link("pages/31_Terms.py", label="Terms", icon="📜")



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



def page_shell(
    what_happened: str,
    why_it_matters: str,
    investigate: str,
    learn_next: str,
) -> None:
    """Standard hierarchy strip across major pages."""
    from mccc.design_system import page_shell_html

    st.markdown(
        page_shell_html(what_happened, why_it_matters, investigate, learn_next),
        unsafe_allow_html=True,
    )


def metric_with_explainer(
    value: str,
    label: str,
    explainer: str,
    *,
    delta: Optional[str] = None,
    delta_kind: str = "flat",
) -> None:
    """Metric card + beginner explainer under it."""
    metric_card(value, label, delta=delta, delta_kind=delta_kind)
    if explainer:
        st.markdown(
            f'<div class="mccc-explainer">{html.escape(explainer)}</div>',
            unsafe_allow_html=True,
        )


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


def safe_error(exc: BaseException, *, fallback: str = "Something went wrong. Please try again.") -> None:
    """User-facing error — never dump raw stack traces."""
    msg = str(exc).strip() if exc else ""
    # Avoid leaking internals / long traces
    if (not msg) or ("Traceback" in msg) or (len(msg) > 280):
        error_banner(fallback)
    else:
        error_banner(msg)


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
    """Page footer with package version + Support / legal links."""
    extra_html = f" · {html.escape(extra)}" if extra else ""
    st.markdown(
        f'<div class="mccc-footer">'
        f'<span class="ver">MCCC v{html.escape(__version__)}</span>'
        f"{extra_html}"
        f" · privacy-first · not financial advice"
        f"</div>",
        unsafe_allow_html=True,
    )
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon="💜")
    with fc2:
        st.page_link("pages/29_About.py", label="About", icon="ℹ️")
    with fc3:
        st.page_link("pages/30_Privacy.py", label="Privacy", icon="🔒")
    with fc4:
        st.page_link("pages/31_Terms.py", label="Terms", icon="📜")


def quick_actions() -> None:
    """Hub quick links to key multipage destinations."""
    cols = st.columns(4)
    with cols[0]:
        st.page_link("pages/18_Search.py", label="Search", icon="🔍")
        st.page_link("pages/24_Intelligence_Center.py", label="Intelligence", icon="🛰️")
    with cols[1]:
        st.page_link("pages/32_Chain_Explorers.py", label="Explorers", icon="🔗")
        st.page_link("pages/4_Wallet_Tracking.py", label="Wallets", icon="👀")
        st.page_link("pages/26_Tokens.py", label="Tokens", icon="🪙")
    with cols[2]:
        st.page_link("pages/27_Calendar.py", label="Calendar", icon="📅")
        st.page_link("pages/3_Airdrop_Tracker.py", label="Airdrops", icon="🪂")
        st.page_link("pages/17_Start_Here.py", label="Start Crypto", icon="🚀")
    with cols[3]:
        st.page_link("pages/2_Project_Tracker.py", label="Projects", icon="📁")
        st.page_link("pages/25_RWA_Intelligence.py", label="RWA", icon="🏛️")
        st.page_link("pages/8_Education.py", label="Academy", icon="📚")
        st.page_link("pages/33_Crypto_Directory.py", label="Crypto Directory", icon="🗂️")
        st.page_link("pages/28_Support_MCCC.py", label="Support MCCC", icon="💜")


def session_user_id():
    try:
        from mccc.auth import get_session_user

        user = get_session_user()
        return user.get("id") if user else None
    except Exception:
        return None


def partner_cta(link: dict, key_prefix: str = "partner", source_page: str = "") -> None:
    """Render CTA via central partner routing — never hardcode referral URLs in pages."""
    from mccc.partners import (
        REFERRAL_LEAVE_DISCLOSURE,
        cta_label,
        record_click,
        resolve_outbound,
    )

    decision = resolve_outbound(link, require_active=True)
    url = decision["url"]
    label = cta_label(link.get("category", "Tools"))
    is_ref = bool(decision.get("used_referral"))
    dest_note = "Partner / referral destination" if is_ref else "Official website"
    lid = link["id"]
    open_key = f"{key_prefix}_open_{lid}"
    track_key = f"{key_prefix}_track_{lid}"

    st.caption(REFERRAL_LEAVE_DISCLOSURE)
    st.caption(f"Outbound: **{dest_note}** · `{url}`")
    if decision.get("official_url") and is_ref:
        st.caption(f"Official (verify yourself): `{decision['official_url']}`")
    col_a, col_b = st.columns((1, 1))
    with col_a:
        if st.button("Track & open", key=track_key, use_container_width=True):
            try:
                record_click(lid, source_page=source_page or key_prefix)
                st.session_state[open_key] = url
                st.success("Visit logged (platform / category / date only — no IP / fingerprint).")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not log visit: {exc}")
    with col_b:
        st.link_button(label, url, use_container_width=True)
    if st.session_state.get(open_key):
        st.link_button("Open now", st.session_state[open_key], type="primary", use_container_width=True)


def referral_leave_disclosure() -> None:
    """Show leave-to-external-platform disclosure on decision surfaces."""
    from mccc.partners import REFERRAL_LEAVE_DISCLOSURE

    st.info(REFERRAL_LEAVE_DISCLOSURE)
