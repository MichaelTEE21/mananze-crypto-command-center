"""PRO Architecture — Coming Soon Stripe; limits; $4/mo; never fake payment."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.auth import get_session_user
from mccc.db import get_feature_flags, init_db, set_feature_flag
from mccc.subscriptions import (
    PRO_PAYMENTS_MESSAGE,
    PRO_PRICE_LABEL,
    check_limit,
    free_limits,
    get_or_create_free,
    is_pro,
    set_tier,
    upgrade_cta_markdown,
)
from mccc.ui import footer, hero, page_setup, upgrade_cta

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
      <p style="color:#9aa7b5;"><strong>{PRO_PAYMENTS_MESSAGE}</strong>
      There is no card capture, no billing backend, and no fake “payment succeeded” state.</p>
      <ul style="color:#cfd8e3;">
        <li>Unlimited projects / wallets / airdrops (soft FREE caps lifted)</li>
        <li>Advanced analytics &amp; CSV export</li>
        <li>Wallet / watchlist alerts</li>
        <li>Extended AI research checklists</li>
        <li>Portfolio sync architecture</li>
      </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b = st.columns(2)
with col_a:
    st.button(
        f"Upgrade to PRO · {PRO_PRICE_LABEL} — Coming Soon",
        disabled=True,
        use_container_width=True,
    )
with col_b:
    st.caption(f"{PRO_PAYMENTS_MESSAGE} Checkout intentionally disabled.")

st.warning(PRO_PAYMENTS_MESSAGE)

st.info(
    f"Current local tier: **{sub.get('tier')}** · provider=`{sub.get('provider')}` · "
    f"PRO active={is_pro(user_id=uid)}"
)

st.subheader("Free soft limits")
limits = free_limits()
for resource in ("projects", "wallets", "airdrops"):
    gate = check_limit(resource, user_id=uid)
    if gate.get("unlimited"):
        st.success(f"**{resource}**: PRO unlimited (count={gate['count']})")
    elif gate["allowed"]:
        st.write(f"**{resource}**: {gate['count']}/{gate['limit']} — {gate['remaining']} left")
    else:
        st.error(gate["message"])
        upgrade_cta(gate["message"])

st.caption(upgrade_cta_markdown())

st.subheader("Local architecture unlock (not payment)")
env_unlock = os.environ.get("MCCC_PRO_UNLOCK", "0") == "1"
if env_unlock:
    st.success("MCCC_PRO_UNLOCK=1 — all PRO features treated as enabled this session (still not a payment).")

c1, c2 = st.columns(2)
with c1:
    if st.button("Set local tier → pro (architecture)", disabled=env_unlock):
        set_tier("pro", user_id=uid)
        for flag in get_feature_flags():
            set_feature_flag(flag["key"], True)
        st.success("Local tier set to pro — still not a payment. No charge occurred.")
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
footer("PRO Architecture")
