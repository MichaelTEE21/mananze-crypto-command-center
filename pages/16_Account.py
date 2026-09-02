"""Account — register / login / logout / profile / onboarding / password / delete."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.auth import (
    authenticate,
    change_password,
    delete_account,
    get_session_user,
    get_user_by_id,
    login,
    logout,
    maybe_bootstrap_admin,
    register_user,
    set_session_user,
    update_profile,
)
from mccc.subscriptions import free_limits, get_or_create_free, is_pro
from mccc.ui import empty_state, error_banner, footer, hero, page_setup, seed_phrase_warning

page_setup("account", "Account")
hero(
    "Account",
    "Optional local profiles. App works without login (guest / single-user). "
    "App password ≠ wallet keys — never enter seeds or private keys.",
)
seed_phrase_warning()
maybe_bootstrap_admin()

user = get_session_user()

tab_auth, tab_profile, tab_security, tab_onboard = st.tabs(
    ["Login / Register", "Profile", "Security", "Onboarding"]
)

with tab_auth:
    st.caption(
        "Session helpers: `get_session_user` / `login` / `logout`. "
        "Guest mode keeps free-tier soft limits; signing in enables multi-profile."
    )
    if user:
        st.success(f"Signed in as **{user.get('email')}**")
        if user.get("is_admin"):
            st.info("Admin flag active (`is_admin`). Partner / Admin panels unlocked for this user.")
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
                password = st.text_input("Password (app only)", type="password", key="login_pw")
                st.caption("This is your MCCC app password — not a wallet, exchange, or seed phrase.")
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
                st.caption("Never paste seed phrases or private keys into any field.")
                if st.form_submit_button("Create account", type="primary"):
                    try:
                        uid = register_user(email, password, display_name=display_name)
                        u = authenticate(email, password)
                        if u:
                            set_session_user(u)
                            get_or_create_free(user_id=uid)
                            maybe_bootstrap_admin()
                            fresh = get_user_by_id(uid)
                            if fresh:
                                set_session_user(fresh)
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
        limits = free_limits()
        st.caption(
            f"Free soft limits (when not PRO): "
            f"{limits['projects']} projects · {limits['wallets']} wallets · {limits['airdrops']} airdrops"
        )
        with st.form("update_profile"):
            display_name = st.text_input("Display name", value=fresh.get("display_name") or "")
            levels = ["", "beginner", "intermediate", "advanced"]
            cur_exp = fresh.get("experience_level") or ""
            experience = st.selectbox(
                "Experience level",
                levels,
                index=levels.index(cur_exp) if cur_exp in levels else 0,
            )
            if st.form_submit_button("Save profile", type="primary"):
                try:
                    updated = update_profile(
                        fresh["id"],
                        display_name=display_name,
                        experience_level=experience,
                    )
                    set_session_user(updated)
                    st.success("Profile updated.")
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    error_banner(str(exc))

with tab_security:
    st.markdown(
        """
        ### Password change
        Uses **scrypt** (stdlib). App password only — never your wallet seed or exchange password.
        """
    )
    if not user:
        empty_state("Not signed in", "Login to change password or delete account.")
    else:
        with st.form("change_pw"):
            cur = st.text_input("Current password", type="password")
            new1 = st.text_input("New password (min 8)", type="password")
            new2 = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Change password", type="primary"):
                if new1 != new2:
                    error_banner("New passwords do not match.")
                else:
                    try:
                        change_password(user["id"], cur, new1)
                        st.success("Password updated.")
                    except Exception as exc:  # noqa: BLE001
                        error_banner(str(exc))

        st.divider()
        st.subheader("Delete account")
        st.warning(
            "Soft-deletes your user row (scrubbed password, `deleted_at` set) and removes "
            "user-scoped portfolio / watchlist / alerts / notifications / education / subscriptions. "
            "Shared projects / airdrops / wallets stay on this local DB."
        )
        with st.form("delete_acct"):
            confirm = st.text_input("Type DELETE to confirm")
            pw = st.text_input("Confirm with password", type="password")
            if st.form_submit_button("Delete my account", type="primary"):
                if confirm.strip() != "DELETE":
                    error_banner("Type DELETE exactly to confirm.")
                else:
                    try:
                        delete_account(user["id"], password=pw, hard=False)
                        st.success("Account deleted. You are signed out.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        error_banner(str(exc))

with tab_onboard:
    st.markdown(
        """
        ### Quick questionnaire
        Helps tailor Start Here recommendations. Stored locally only.
        Goals + experience feed beginner/advanced copy — never financial advice.
        """
    )
    if not user:
        st.caption("Sign in to save onboarding answers to your profile (optional).")
    saved = ""
    if user:
        fresh = get_user_by_id(user["id"]) or user
        saved = fresh.get("onboarding_goals") or ""
    saved = st.session_state.get("mccc_onboarding") or saved
    # Parse simple blob goals=a,b; risk=x; chains=y
    default_goals = []
    default_risk = "low"
    default_chains = ""
    if saved:
        for part in saved.split(";"):
            part = part.strip()
            if part.startswith("goals="):
                default_goals = [g for g in part[6:].split(",") if g]
            elif part.startswith("risk="):
                default_risk = part[5:] or "low"
            elif part.startswith("chains="):
                default_chains = part[7:]
    goal_opts = [
        "Learn basics",
        "Track airdrops",
        "Research projects",
        "Portfolio notes",
        "Security hygiene",
    ]
    goals = st.multiselect(
        "Goals",
        goal_opts,
        default=[g for g in default_goals if g in goal_opts],
    )
    risk = st.select_slider(
        "Risk comfort (self-reported)",
        options=["low", "medium", "high"],
        value=default_risk if default_risk in ("low", "medium", "high") else "low",
    )
    chains = st.text_input("Chains of interest", value=default_chains, placeholder="ethereum, solana…")
    experience_onboard = st.selectbox(
        "Experience (also saved to profile when signed in)",
        ["", "beginner", "intermediate", "advanced"],
    )
    if st.button("Save onboarding", type="primary"):
        blob = f"goals={','.join(goals)}; risk={risk}; chains={chains}"
        try:
            if user:
                update_profile(
                    user["id"],
                    onboarding_goals=blob,
                    experience_level=experience_onboard or None,
                )
                set_session_user(get_user_by_id(user["id"]) or user)
            else:
                # guest: session only — still refuse secrets
                from mccc.security import reject_sensitive_credential

                reject_sensitive_credential(blob, field="onboarding")
            st.session_state["mccc_onboarding"] = blob
            st.success("Saved locally.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))
    if st.session_state.get("mccc_onboarding") or (user and (get_user_by_id(user["id"]) or {}).get("onboarding_goals")):
        st.info(st.session_state.get("mccc_onboarding") or (get_user_by_id(user["id"]) or {}).get("onboarding_goals"))

st.caption(
    "Admin bootstrap: set `MCCC_BOOTSTRAP_ADMIN_EMAIL` to your account email "
    "(or `app_settings.bootstrap_admin_email`) so the first matching user gets `is_admin`."
)
st.page_link("pages/17_Start_Here.py", label="Continue to Start Here", icon="🚀")
st.page_link("pages/10_PRO_Architecture.py", label="PRO Architecture", icon="⭐")
footer("Account")
