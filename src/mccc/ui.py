"""Shared premium dark UI helpers for Streamlit pages."""
from __future__ import annotations

import streamlit as st

from mccc import APP_NAME, APP_TAGLINE, __version__
from mccc.db import init_db, log_event
from mccc.demo_data import DEMO_BANNER


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}
.mccc-hero {
  background: linear-gradient(135deg, #0b0f14 0%, #12202b 45%, #0d281f 100%);
  border: 1px solid #1e2a36;
  border-radius: 16px;
  padding: 1.4rem 1.6rem;
  margin-bottom: 1rem;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.mccc-hero h1 {
  margin: 0;
  font-size: 1.65rem;
  letter-spacing: 0.04em;
  color: #e8eef5;
}
.mccc-hero .tag {
  color: #00d4aa;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  margin-top: 0.35rem;
}
.mccc-hero .sub {
  color: #9aa7b5;
  margin-top: 0.55rem;
  font-size: 0.95rem;
}
.mccc-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  background: #1a2e28;
  color: #00d4aa;
  border: 1px solid #00d4aa55;
}
.mccc-badge-warn {
  background: #2e241a;
  color: #ffb020;
  border-color: #ffb02055;
}
.mccc-badge-pro {
  background: #241a2e;
  color: #c4a0ff;
  border-color: #c4a0ff55;
}
.mccc-card {
  background: #141a22;
  border: 1px solid #243040;
  border-radius: 12px;
  padding: 1rem 1.1rem;
  margin-bottom: 0.75rem;
}
.mccc-metric {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.35rem;
  color: #00d4aa;
}
div[data-testid="stSidebar"] {
  background: #0a0e13;
  border-right: 1px solid #1e2a36;
}
</style>
"""


def inject_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


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
    with st.sidebar:
        st.markdown(f"**{APP_NAME}**")
        st.caption(f"{APP_TAGLINE} · v{__version__}")
        st.markdown('<span class="mccc-badge">LOCAL · PRIVACY-FIRST</span>', unsafe_allow_html=True)
        st.divider()
        st.caption("B=MananzeZA · never stores seeds / private keys")


def hero(title: str, subtitle: str = "", show_demo_banner: bool = False) -> None:
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


def demo_callout(text: str | None = None) -> None:
    st.warning(text or DEMO_BANNER)


def pro_locked_panel(feature_name: str) -> None:
    st.markdown(
        f"""
        <div class="mccc-card">
          <span class="mccc-badge-pro">PRO ARCHITECTURE</span>
          <p style="margin-top:0.6rem;color:#cfd8e3;"><strong>{feature_name}</strong> is gated in the PRO mock.
          No payment is processed. Toggle flags in <em>PRO Architecture</em> or set
          <code>MCCC_PRO_UNLOCK=1</code> locally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
