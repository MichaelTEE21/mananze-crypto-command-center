"""PRO Architecture — Coming Soon Stripe; limits; $4/mo; never fake payment."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.auth import get_session_user
from mccc.db import get_feature_flags, init_db, set_feature_flag
from mccc.subscriptions import PRO_PRICE_LABEL, get_or_create_free, is_pro, set_tier
from mccc.ui import hero, page_setup

page_setup("pro_architecture", "PRO Architecture")
hero(
    "PRO Architecture",
    f"Feature flags & Coming Soon Stripe ({PRO_PRICE_LABEL}) — architecture only, not charged.",
)

init_db()
user = get_session_user()
uid = user.get("id") if user else None
sub = get_or_create_free(user_id=uid)

st.markdown(
    '<span class="mccc-badge-pro">NO PAYMENT PROCESSING</span> '
    '<span class="mccc-badge-warn">STRIPE COMING SOON</span> '
    '<span class="mccc-badge">ARCHITECTURE / NOT CHARGED</span>',
    unsafe_allow_html=True,
)

st.subheader("MCCC PRO")
st.markdown(
    f"""
    <div class="mccc-card">
      <h3 style="margin-top:0;color:#c4a0ff;">PRO · {PRO_PRICE_LABEL} (planned)</h3>
      <p style="color:#9aa7b5;">Stripe checkout is <strong>Coming Soon</strong>. There is no card capture,
      no billing backend, and no fake “payment succeeded” state.</p>
      <ul style="color:#cfd8e3;">
        <li>Advanced analytics &amp; export</li>
        <li>Wallet / watchlist alerts</li>
        <li>Extended research checklists</li>
        <li>Portfolio sync architecture</li>
      </ul>
      <p style="color:#9aa7b5;font-size:0.85rem;">Free tier limits (soft): local SQLite only; no multi-device sync;
      LLM assist requires your own AI_API_KEY.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2)
with col_a:
    st.button(f"Upgrade to PRO · {PRO_PRICE_LABEL} — Coming Soon", disabled=True, use_container_width=True)
with col_b:
    st.caption("Checkout intentionally disabled. Never fakes a successful payment.")

st.info(f"Current local tier: **{sub.get('tier')}** · provider=`{sub.get('provider')}` · PRO active={is_pro(user_id=uid)}")

st.subheader("Local architecture unlock (not payment)")
env_unlock = os.environ.get("MCCC_PRO_UNLOCK", "0") == "1"
if env_unlock:
    st.success("MCCC_PRO_UNLOCK=1 — all PRO features treated as enabled this session.")

c1, c2 = st.columns(2)
with c1:
    if st.button("Set local tier → pro (architecture)", disabled=env_unlock):
        set_tier("pro", user_id=uid)
        # also flip flags for convenience
        for flag in get_feature_flags():
            set_feature_flag(flag["key"], True)
        st.success("Local tier set to pro — still not a payment.")
        st.rerun()
with c2:
    if st.button("Set local tier → free"):
        set_tier("free", user_id=uid)
        st.rerun()

st.subheader("Feature flags (local)")
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

st.caption("Toggles write to SQLite feature_flags. Still: architecture / not charged.")
