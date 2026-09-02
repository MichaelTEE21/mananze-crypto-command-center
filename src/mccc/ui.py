"""Shared premium dark UI helpers for Streamlit pages."""
from __future__ import annotations

import os

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

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}
.mccc-hero {
  background: linear-gradient(135deg, #0b0f14 0%, #12202b 45%, #0d281f 100%);
  border: 1px solid #1e2a36;
  border-radius: 14px;
  padding: 1.15rem 1.35rem;
  margin-bottom: 0.85rem;
  box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}
.mccc-hero h1 {
  margin: 0;
  font-size: 1.5rem;
  letter-spacing: 0.04em;
  color: #e8eef5;
}
.mccc-hero .tag {
  color: #00d4aa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  margin-top: 0.3rem;
}
.mccc-hero .sub {
  color: #9aa7b5;
  margin-top: 0.45rem;
  font-size: 0.9rem;
}
.mccc-badge {
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  background: #1a2e28;
  color: #00d4aa;
  border: 1px solid #00d4aa55;
  margin-right: 0.25rem;
}
.mccc-badge-warn {
  background: #2e241a;
  color: #ffb020;
  border: 1px solid #ffb02055;
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin-right: 0.25rem;
}
.mccc-badge-pro {
  background: #241a2e;
  color: #c4a0ff;
  border: 1px solid #c4a0ff55;
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin-right: 0.25rem;
}
.mccc-badge-live {
  background: #0f2a1c;
  color: #3dffb5;
  border: 1px solid #3dffb555;
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin-right: 0.25rem;
}
.mccc-badge-demo {
  background: #2a2210;
  color: #ffcc66;
  border: 1px solid #ffcc6655;
  display: inline-block;
  padding: 0.12rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin-right: 0.25rem;
}
.mccc-card {
  background: #121820;
  border: 1px solid #243040;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  margin-bottom: 0.55rem;
}
.mccc-metric {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem;
  color: #00d4aa;
  line-height: 1.2;
}
.mccc-metric-label {
  color: #9aa7b5;
  font-size: 0.78rem;
  margin-top: 0.2rem;
}
.mccc-empty {
  background: #10161e;
  border: 1px dashed #2a3848;
  border-radius: 10px;
  padding: 1.1rem 1.2rem;
  text-align: center;
  color: #9aa7b5;
  margin: 0.5rem 0 0.75rem;
}
.mccc-empty strong { color: #e8eef5; display: block; margin-bottom: 0.35rem; }
.mccc-error {
  background: #2a1414;
  border: 1px solid #5a2020;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  color: #ffb0b0;
  margin: 0.4rem 0 0.7rem;
  font-size: 0.9rem;
}
.mccc-kanban {
  background: #10161e;
  border: 1px solid #243040;
  border-radius: 8px;
  padding: 0.55rem 0.65rem;
  margin-bottom: 0.45rem;
  min-height: 3.2rem;
}
.mccc-kanban .title { color: #e8eef5; font-weight: 600; font-size: 0.88rem; }
.mccc-kanban .meta { color: #8a97a6; font-size: 0.75rem; margin-top: 0.2rem; }
div[data-testid="stSidebar"] {
  background: #0a0e13;
  border-right: 1px solid #1e2a36;
}
div[data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace;
}
</style>
"""


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
        page_icon="⬡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_db()
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
        st.caption("B=MananzeZA · never stores seeds / private keys")


def hero(title: str, subtitle: str = "", show_demo_banner: bool = False) -> None:
    from mccc.demo_data import DEMO_BANNER

    demo_html = ""
    if show_demo_banner:
        demo_html = f'<div class="tag">{DEMO_BANNER}</div>'
    st.markdown(
        f"""
        <div class="mccc-hero">
          <span class="mccc-badge">MCCC</span>
          <h1>{title}</h1>
          <div class="sub">{subtitle}</div>
          {demo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, hint: str = "") -> None:
    hint_html = f"<div>{hint}</div>" if hint else ""
    st.markdown(
        f'<div class="mccc-empty"><strong>{title}</strong>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def error_banner(msg: str) -> None:
    st.markdown(f'<div class="mccc-error">{msg}</div>', unsafe_allow_html=True)


def loading(caption: str = "Loading…") -> None:
    st.caption(f"⏳ {caption}")


def live_or_demo_badge(is_live: bool) -> None:
    if is_live:
        st.markdown('<span class="mccc-badge-live">LIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mccc-badge-demo">DEMO</span>', unsafe_allow_html=True)


def demo_callout(text: str | None = None) -> None:
    from mccc.demo_data import DEMO_BANNER

    st.warning(text or DEMO_BANNER)


def pro_locked_panel(feature_name: str) -> None:
    st.markdown(
        f"""
        <div class="mccc-card">
          <span class="mccc-badge-pro">PRO ARCHITECTURE</span>
          <p style="margin-top:0.55rem;color:#cfd8e3;"><strong>{feature_name}</strong> is gated.
          Stripe checkout is <em>Coming Soon</em> ($4/mo planned). No payment is processed.
          Toggle flags in <em>PRO Architecture</em> or set <code>MCCC_PRO_UNLOCK=1</code> locally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def metric_card(value: str, label: str) -> None:
    st.markdown(
        f'<div class="mccc-card"><div class="mccc-metric">{value}</div>'
        f'<div class="mccc-metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


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
