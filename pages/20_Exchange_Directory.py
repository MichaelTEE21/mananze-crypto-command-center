"""Exchange Directory — official_url vs referral_url; Track & open; admin CRUD gate."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from mccc.auth import get_session_user
from mccc.db import init_db
from mccc.exchanges import (
    STATUSES,
    TYPES,
    add_exchange,
    delete_exchange,
    list_exchanges,
    resolve_visit_url,
    seed_demo_exchanges,
    set_exchange_status,
    update_exchange,
)
from mccc.ui import (
    footer,
    affiliate_disclosure,
    demo_callout,
    empty_state,
    hero,
    page_setup,
    section_header,
    seed_phrase_warning,
)

DEMO_ADMIN_PASSWORD = "mccc-admin-demo"


def _admin_password() -> str:
    return os.environ.get("MCCC_ADMIN_PASSWORD") or DEMO_ADMIN_PASSWORD


def _is_admin() -> bool:
    if st.session_state.get("mccc_admin_unlocked"):
        return True
    user = get_session_user()
    if user and user.get("is_admin"):
        return True
    return False


page_setup("exchange_directory", "Exchange Directory")
hero(
    "Exchange Directory",
    "CEX / DEX research listings from the local `exchanges` table. official_url ≠ hardcoded referral.",
    show_demo_banner=True,
)

init_db()
seed_demo_exchanges()
affiliate_disclosure()
seed_phrase_warning()
demo_callout("DEMO rows use example.com — not live trading venues. Verify every URL yourself.")

st.caption(
    "Referral placement does **not** mean an exchange is safer or better. "
    "MCCC never asks for exchange passwords or 2FA secrets."
)

# Filters
rows = list_exchanges()
fc1, fc2 = st.columns(2)
type_f = fc1.selectbox("Type", ["(all)"] + list(TYPES))
status_f = fc2.selectbox("Status", ["(all)"] + list(STATUSES), index=1 if "Active" in STATUSES else 0)

filtered = []
for r in rows:
    if type_f != "(all)" and r.get("type") != type_f:
        continue
    if status_f != "(all)" and r.get("status") != status_f:
        continue
    filtered.append(r)

section_header(f"Exchanges ({len(filtered)} / {len(rows)})", "Official vs referral shown clearly")
if not filtered:
    empty_state("No exchanges match", "Clear filters or seed DEMO rows (auto on empty DB).")
else:
    for ex in filtered:
        with st.container():
            is_ref = bool((ex.get("referral_url") or "").strip())
            badge = "REFERRAL DEST" if is_ref else "OFFICIAL ONLY"
            demo_tag = " · DEMO" if "DEMO" in (ex.get("name") or "").upper() else ""
            st.markdown(
                f"**{ex['name']}** · `{ex.get('type')}` · `{ex.get('status')}` "
                f'<span class="mccc-badge">{badge}{demo_tag}</span>',
                unsafe_allow_html=True,
            )
            if ex.get("description"):
                st.write(ex["description"])
            meta = []
            if ex.get("region"):
                meta.append(f"Region: {ex['region']}")
            if ex.get("difficulty"):
                meta.append(f"Difficulty: {ex['difficulty']}")
            if ex.get("chains"):
                meta.append(f"Chains: {ex['chains']}")
            if ex.get("assets"):
                meta.append(f"Assets: {ex['assets']}")
            if meta:
                st.caption(" · ".join(meta))
            if ex.get("security_info"):
                st.info(ex["security_info"])
            official = (ex.get("official_url") or "").strip()
            referral = (ex.get("referral_url") or "").strip()
            if official:
                st.markdown(f"**Official URL (verify):** [{official}]({official})")
            if referral:
                st.markdown(f"**Referral URL (optional):** `{referral}`")
            else:
                st.caption("No referral URL on file — visit uses official only.")
            if ex.get("docs_url"):
                st.caption(f"Docs: {ex['docs_url']}")

            visit = resolve_visit_url(ex)
            dest_note = "Partner / referral destination" if is_ref else "Official website"
            st.caption(f"Outbound: **{dest_note}** · `{visit}`")
            col_a, col_b = st.columns(2)
            track_key = f"ex_track_{ex['id']}"
            open_key = f"ex_open_{ex['id']}"
            with col_a:
                if st.button("Track & open", key=track_key, use_container_width=True):
                    # Local track: session only (no partner_link_clicks table for exchanges)
                    st.session_state[open_key] = visit
                    st.session_state.setdefault("exchange_visit_log", [])
                    st.session_state["exchange_visit_log"].append(
                        {"id": ex["id"], "name": ex["name"], "url": visit}
                    )
                    st.success("Visit noted in session (no IP / fingerprint).")
            with col_b:
                label = "Join Exchange" if ex.get("type") == "CEX" else "Explore DEX"
                st.link_button(label, visit, use_container_width=True)
            if st.session_state.get(open_key):
                st.link_button(
                    "Open now",
                    st.session_state[open_key],
                    type="primary",
                    use_container_width=True,
                )
            st.divider()

# --- Admin CRUD ---
section_header("Admin CRUD", "Gated by MCCC_ADMIN_PASSWORD or is_admin session user")
if not os.environ.get("MCCC_ADMIN_PASSWORD"):
    st.caption("Unset `MCCC_ADMIN_PASSWORD` → local DEMO gate `mccc-admin-demo`.")

if not _is_admin():
    with st.expander("Unlock admin", expanded=False):
        with st.form("ex_admin_unlock"):
            pw = st.text_input("Admin password", type="password")
            if st.form_submit_button("Unlock"):
                if pw == _admin_password():
                    st.session_state["mccc_admin_unlocked"] = True
                    st.success("Unlocked.")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
else:
    st.success("Admin unlocked for this session.")
    if st.button("Lock admin"):
        st.session_state["mccc_admin_unlocked"] = False
        st.rerun()

    with st.expander("Add exchange", expanded=False):
        with st.form("add_exchange", clear_on_submit=True):
            name = st.text_input("Name")
            type_ = st.selectbox("Type", list(TYPES))
            official_url = st.text_input("Official URL")
            referral_url = st.text_input("Referral URL (optional — leave empty if none)")
            docs_url = st.text_input("Docs URL")
            description = st.text_area("Description")
            c1, c2, c3 = st.columns(3)
            region = c1.text_input("Region")
            difficulty = c2.text_input("Difficulty")
            chains = c3.text_input("Chains")
            assets = st.text_input("Assets")
            security_info = st.text_input("Security info")
            status = st.selectbox("Status", list(STATUSES))
            if st.form_submit_button("Create", type="primary"):
                if not name.strip() or not official_url.strip():
                    st.error("Name and official URL required.")
                else:
                    add_exchange(
                        name,
                        type_=type_,
                        official_url=official_url,
                        referral_url=referral_url,
                        docs_url=docs_url,
                        description=description,
                        region=region,
                        difficulty=difficulty,
                        chains=chains,
                        assets=assets,
                        security_info=security_info,
                        status=status,
                    )
                    st.success("Exchange added.")
                    st.rerun()

    if rows:
        edit_map = {f"#{r['id']} {r['name']}": r for r in rows}
        pick = st.selectbox("Edit exchange", list(edit_map.keys()))
        cur = edit_map[pick]
        with st.form("edit_exchange"):
            name = st.text_input("Name", value=cur["name"])
            type_ = st.selectbox(
                "Type",
                list(TYPES),
                index=list(TYPES).index(cur["type"]) if cur.get("type") in TYPES else 0,
            )
            official_url = st.text_input("Official URL", value=cur.get("official_url") or "")
            referral_url = st.text_input("Referral URL", value=cur.get("referral_url") or "")
            docs_url = st.text_input("Docs URL", value=cur.get("docs_url") or "")
            description = st.text_area("Description", value=cur.get("description") or "")
            region = st.text_input("Region", value=cur.get("region") or "")
            difficulty = st.text_input("Difficulty", value=cur.get("difficulty") or "")
            chains = st.text_input("Chains", value=cur.get("chains") or "")
            assets = st.text_input("Assets", value=cur.get("assets") or "")
            security_info = st.text_input("Security info", value=cur.get("security_info") or "")
            status = st.selectbox(
                "Status",
                list(STATUSES),
                index=list(STATUSES).index(cur["status"]) if cur.get("status") in STATUSES else 0,
            )
            a, b, c = st.columns(3)
            if a.form_submit_button("Save", type="primary"):
                update_exchange(
                    cur["id"],
                    name=name,
                    type_=type_,
                    official_url=official_url,
                    referral_url=referral_url,
                    docs_url=docs_url,
                    description=description,
                    region=region,
                    difficulty=difficulty,
                    chains=chains,
                    assets=assets,
                    security_info=security_info,
                    status=status,
                )
                st.success("Updated.")
                st.rerun()
            if b.form_submit_button("Disable"):
                set_exchange_status(cur["id"], "Disabled")
                st.warning("Disabled.")
                st.rerun()
            if c.form_submit_button("Delete"):
                delete_exchange(cur["id"])
                st.warning("Deleted.")
                st.rerun()

footer("Exchange Directory")
