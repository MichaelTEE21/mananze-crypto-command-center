"""Stage 10 — PRO architecture: feature flags + paywall mock (no payments)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.db import get_feature_flags, init_db, set_feature_flag
from mccc.ui import hero, page_setup

page_setup("pro_architecture", "PRO Architecture")
hero(
    "PRO Architecture",
    "Feature flags & paywall UI mock — architecture only, not charged.",
)

init_db()
st.markdown(
    '<span class="mccc-badge-pro">NO PAYMENT PROCESSING</span> '
    '<span class="mccc-badge-warn">ARCHITECTURE / NOT CHARGED</span>',
    unsafe_allow_html=True,
)

st.subheader("Paywall mock")
st.markdown(
    """
    <div class="mccc-card">
      <h3 style="margin-top:0;color:#c4a0ff;">MCCC PRO (mock)</h3>
      <p style="color:#9aa7b5;">Unlock advanced analytics, wallet alerts mock, deep research checklists,
      and portfolio sync architecture. This screen demonstrates gating — there is no checkout,
      no card capture, and no billing backend.</p>
      <ul style="color:#cfd8e3;">
        <li>Advanced analytics &amp; export</li>
        <li>Wallet alerts (mock)</li>
        <li>Extended research checklists</li>
        <li>Portfolio sync architecture</li>
      </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2)
with col_a:
    st.button("Upgrade to PRO — disabled mock", disabled=True, use_container_width=True)
with col_b:
    st.caption("Button is intentionally disabled. Use flags below for local unlock.")

st.subheader("Feature flags (local)")
env_unlock = os.environ.get("MCCC_PRO_UNLOCK", "0") == "1"
if env_unlock:
    st.success("MCCC_PRO_UNLOCK=1 — all PRO features treated as enabled this session.")

flags = get_feature_flags()
for flag in flags:
    key = flag["key"]
    enabled = bool(flag["enabled"])
    new_val = st.toggle(
        f"{key} — {flag['description']}",
        value=enabled,
        key=f"flag_{key}",
        disabled=env_unlock,
    )
    if not env_unlock and new_val != enabled:
        set_feature_flag(key, new_val)
        st.rerun()

st.info(
    "Toggles write to SQLite feature_flags. Pages such as Analytics and AI Assistant "
    "read these flags for PRO panels. Still: architecture / not charged."
)
