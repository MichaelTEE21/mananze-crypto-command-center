"""Account — register / login / logout / profile / onboarding."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.auth import (
    authenticate,
    get_session_user,
    get_user_by_id,
    login,
    logout,
    register_user,
    set_session_user,
)
from mccc.db import connect, utc_now
from mccc.subscriptions import get_or_create_free, is_pro
from mccc.ui import empty_state, error_banner, hero, page_setup, seed_phrase_warning

page_setup("account", "Account")
hero(
    "Account",
    "Optional local profiles. App works without login (single-user). Never enter seeds or private keys.",
)
seed_phrase_warning()

user = get_session_user()

tab_auth, tab_profile, tab_onboard = st.tabs(["Login / Register", "Profile", "Onboarding"])

with tab_auth:
    if user:
        st.success(f"Signed in as **{user.get('email')}**")
        if st.button("Log out", type="primary"):
            logout()
            st.rerun()
    else:
        st.info("Guest mode active — portfolio / watchlist use nullable user_id until you sign in.")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Login")
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pw")
                if st.form_submit_button("Login", type="primary"):
                    try:
                        u = login(email, password)
                        if u:
                            get_or_create_free(user_id=u["id"])
                            st.success("Logged in.")
                            st.rerun()
                        else:
                            error_banner("Invalid email or password.")
                    except Exception as exc:  # noqa: BLE001
                        error_banner(str(exc))
        with c2:
            st.subheader("Register")
            with st.form("reg_form"):
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password (min 8)", type="password", key="reg_pw")
                display_name = st.text_input("Display name")
                if st.form_submit_button("Create account", type="primary"):
                    try:
                        uid = register_user(email, password, display_name=display_name)
                        u = authenticate(email, password)
                        if u:
                            set_session_user(u)
                            get_or_create_free(user_id=uid)
                        st.success("Account created & signed in.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        error_banner(str(exc))

with tab_profile:
    if not user:
        empty_state("Not signed in", "Register or login to manage a multi-profile account.")
    else:
        fresh = get_user_by_id(user["id"]) or user
        st.write(f"**Email:** {fresh.get('email')}")
        st.write(f"**Display name:** {fresh.get('display_name') or '—'}")
        st.write(f"**Experience:** {fresh.get('experience_level') or '—'}")
        st.write(f"**Admin:** {'yes' if fresh.get('is_admin') else 'no'}")
        st.write(f"**PRO tier (local):** {'yes' if is_pro(user_id=fresh['id']) else 'no'}")
        with st.form("update_profile"):
            display_name = st.text_input("Display name", value=fresh.get("display_name") or "")
            experience = st.selectbox(
                "Experience level",
                ["", "beginner", "intermediate", "advanced"],
                index=["", "beginner", "intermediate", "advanced"].index(
                    fresh.get("experience_level") or ""
                )
                if (fresh.get("experience_level") or "") in ["", "beginner", "intermediate", "advanced"]
                else 0,
            )
            if st.form_submit_button("Save profile", type="primary"):
                lowered = (display_name or "").lower()
                if any(x in lowered for x in ("seed", "private key", "mnemonic")):
                    error_banner("Seed phrases and private keys are not allowed.")
                else:
                    with connect() as conn:
                        conn.execute(
                            """UPDATE users SET display_name=?, experience_level=?, updated_at=?
                               WHERE id=?""",
                            (display_name.strip(), experience, utc_now(), fresh["id"]),
                        )
                    set_session_user(get_user_by_id(fresh["id"]) or fresh)
                    st.success("Profile updated.")
                    st.rerun()

with tab_onboard:
    st.markdown(
        """
        ### Quick questionnaire
        Helps tailor Start Here recommendations. Stored locally only.
        """
    )
    if not user:
        st.caption("Sign in to save onboarding answers to your profile (optional).")
    goals = st.multiselect(
        "Goals",
        ["Learn basics", "Track airdrops", "Research projects", "Portfolio notes", "Security hygiene"],
    )
    risk = st.select_slider("Risk comfort (self-reported)", options=["low", "medium", "high"], value="low")
    chains = st.text_input("Chains of interest", placeholder="ethereum, solana…")
    if st.button("Save onboarding", type="primary"):
        blob = f"goals={','.join(goals)}; risk={risk}; chains={chains}"
        if any(x in blob.lower() for x in ("seed", "private key", "mnemonic")):
            error_banner("Seed phrases and private keys are not allowed.")
        else:
            st.session_state["mccc_onboarding"] = blob
            if user:
                with connect() as conn:
                    conn.execute(
                        "UPDATE users SET onboarding_goals=?, updated_at=? WHERE id=?",
                        (blob, utc_now(), user["id"]),
                    )
                set_session_user(get_user_by_id(user["id"]) or user)
            st.success("Saved locally.")
    if st.session_state.get("mccc_onboarding") or (user and user.get("onboarding_goals")):
        st.info(st.session_state.get("mccc_onboarding") or user.get("onboarding_goals"))

st.page_link("pages/17_Start_Here.py", label="Continue to Start Here", icon="🚀")
