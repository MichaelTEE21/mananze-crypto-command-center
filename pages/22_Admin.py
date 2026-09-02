"""Admin panel — announcements, featured settings, seed exchanges, flags, resources CRUD."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.announcements import (
    create as create_announcement,
    delete as delete_announcement,
    expire as expire_announcement,
    list_all as list_announcements,
    publish as publish_announcement,
    update as update_announcement,
)
from mccc.auth import get_session_user
from mccc.db import (
    get_feature_flags,
    get_setting,
    init_db,
    list_projects,
    list_settings,
    set_feature_flag,
    set_setting,
)
from mccc.exchanges import seed_demo_exchanges
from mccc.resources import (
    RESOURCE_TYPES,
    add_resource,
    delete_resource,
    list_resources,
    record_resource_click,
    update_resource,
)
from mccc.config import config_status_public, env_flag
from mccc.subscriptions import PRO_PAYMENTS_MESSAGE, get_or_create_free
from mccc import __version__
from mccc.ui import (
    empty_state,
    error_banner,
    footer,
    hero,
    page_setup,
    section_header,
    seed_phrase_warning,
)

DEMO_ADMIN_PASSWORD = "mccc-admin-demo"


def _admin_password() -> str:
    return os.environ.get("MCCC_ADMIN_PASSWORD") or DEMO_ADMIN_PASSWORD


def _is_unlocked() -> bool:
    if st.session_state.get("mccc_admin_unlocked"):
        return True
    user = get_session_user()
    if user and user.get("is_admin"):
        return True
    return False


page_setup("admin", "Admin")
hero(
    "Admin panel",
    "Announcements, featured settings, resources, feature flags, exchange seed. "
    "DEMO password if MCCC_ADMIN_PASSWORD unset.",
)

init_db()
seed_phrase_warning()

if not os.environ.get("MCCC_ADMIN_PASSWORD"):
    st.warning(
        "Using **local DEMO** admin password `mccc-admin-demo` "
        "(set `MCCC_ADMIN_PASSWORD` in `.env` for your own gate). Demo only — not production auth."
    )

if not _is_unlocked():
    st.caption("Unlock with `MCCC_ADMIN_PASSWORD` **or** sign in as an `is_admin` user on Account.")
    with st.form("admin_unlock_main"):
        pw = st.text_input("Admin password", type="password")
        if st.form_submit_button("Unlock", type="primary"):
            if pw == _admin_password():
                st.session_state["mccc_admin_unlocked"] = True
                st.success("Unlocked for this session.")
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

if st.sidebar.button("Lock admin", key="admin_lock_main"):
    st.session_state["mccc_admin_unlocked"] = False
    st.rerun()

st.success("Admin unlocked (session).")

st.markdown(
    "**Quick links:** [Partner Links admin](12_Admin_Partner_Links) · "
    "[Exchange Directory](20_Exchange_Directory) (admin CRUD on that page)"
)

_tab_labels = [
    "Announcements",
    "Featured / settings",
    "Resources",
    "Feature flags",
    "Exchanges seed",
    "Subscription",
]
if env_flag("MCCC_DEV"):
    _tab_labels.append("Diagnostics")
_tabs = st.tabs(_tab_labels)
tab_ann, tab_feat, tab_res, tab_flags, tab_ex, tab_sub = _tabs[:6]
tab_diag = _tabs[6] if len(_tabs) > 6 else None

with tab_ann:
    section_header("Create announcement")
    with st.form("ann_create", clear_on_submit=True):
        title = st.text_input("Title")
        body = st.text_area("Body")
        published = st.checkbox("Published", value=True)
        expires = st.text_input("Expires at (ISO UTC, optional)", placeholder="2026-12-31T00:00:00Z")
        if st.form_submit_button("Create", type="primary"):
            try:
                aid = create_announcement(title, body, published=published, expires_at=expires.strip())
                st.success(f"Created announcement #{aid}")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                error_banner(str(exc))

    rows = list_announcements()
    section_header(f"All announcements ({len(rows)})")
    if not rows:
        empty_state("None yet", "Create one above.")
    else:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        labels = {f"#{r['id']} {r['title']} (pub={r['published']})": r["id"] for r in rows}
        pick = st.selectbox("Select", list(labels.keys()))
        aid = labels[pick]
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("Publish"):
            publish_announcement(aid, True)
            st.rerun()
        if b2.button("Unpublish"):
            publish_announcement(aid, False)
            st.rerun()
        if b3.button("Expire now"):
            expire_announcement(aid)
            st.rerun()
        if b4.button("Delete"):
            delete_announcement(aid)
            st.rerun()
        with st.form("ann_edit"):
            st.caption(f"Edit #{aid}")
            nt = st.text_input("New title", value=next(r["title"] for r in rows if r["id"] == aid))
            nb = st.text_area("New body", value=next((r.get("body") or "") for r in rows if r["id"] == aid))
            ne = st.text_input(
                "New expires_at",
                value=next((r.get("expires_at") or "") for r in rows if r["id"] == aid),
            )
            if st.form_submit_button("Save edits"):
                update_announcement(aid, title=nt, body=nb, expires_at=ne)
                st.success("Updated.")
                st.rerun()

with tab_feat:
    section_header("Admin bootstrap email")
    st.caption("Promote matching Account email to is_admin (also via env MCCC_BOOTSTRAP_ADMIN_EMAIL).")
    cur_boot = get_setting("bootstrap_admin_email", "")
    with st.form("boot_admin_email"):
        boot_email = st.text_input("bootstrap_admin_email", value=cur_boot)
        if st.form_submit_button("Save bootstrap email"):
            set_setting("bootstrap_admin_email", (boot_email or "").strip().lower())
            st.success("Saved. Sign in / reload to apply maybe_bootstrap_admin().")
            st.rerun()

    section_header("Featured / app_settings")
    st.caption("Key/value settings for hub featured content (no secrets).")
    featured_title = st.text_input(
        "featured_title",
        value=get_setting("featured_title", "MCCC research cockpit"),
    )
    featured_body = st.text_area(
        "featured_body",
        value=get_setting("featured_body", "Track projects, airdrops, and education locally."),
    )
    hub_banner = st.text_input(
        "hub_banner",
        value=get_setting("hub_banner", ""),
        placeholder="Optional Command Center banner text",
    )
    if st.button("Save featured settings", type="primary"):
        set_setting("featured_title", featured_title)
        set_setting("featured_body", featured_body)
        set_setting("hub_banner", hub_banner)
        st.success("Settings saved.")
    all_s = list_settings()
    if all_s:
        st.dataframe(
            pd.DataFrame([{"key": k, "value": v} for k, v in all_s.items()]),
            use_container_width=True,
            hide_index=True,
        )

with tab_res:
    section_header("Resources CRUD")
    projects = list_projects()
    proj_map = {"(none)": None}
    for p in projects:
        proj_map[f"#{p['id']} {p['name']}"] = p["id"]

    with st.form("res_add", clear_on_submit=True):
        rt = st.text_input("Title")
        ru = st.text_input("URL")
        rtype = st.selectbox("Type", list(RESOURCE_TYPES))
        rproj = st.selectbox("Project", list(proj_map.keys()))
        rdesc = st.text_input("Description")
        roff = st.checkbox("Official", value=False)
        if st.form_submit_button("Add resource", type="primary"):
            try:
                rid = add_resource(
                    rt,
                    url=ru,
                    resource_type=rtype,
                    project_id=proj_map[rproj],
                    description=rdesc,
                    is_official=roff,
                )
                st.success(f"Added resource #{rid}")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                error_banner(str(exc))

    q = st.text_input("Search resources", placeholder="docs, audit…")
    resources = list_resources(q=q.strip() or None)
    if not resources:
        empty_state("No resources", "Add one above.")
    else:
        st.dataframe(pd.DataFrame(resources), use_container_width=True, hide_index=True)
        rlabels = {f"#{r['id']} {r['title']}": r for r in resources}
        rp = st.selectbox("Manage resource", list(rlabels.keys()))
        row = rlabels[rp]
        e1, e2, e3 = st.columns(3)
        if e1.button("Track click (+1)"):
            record_resource_click(row["id"])
            st.rerun()
        if e2.button("Toggle official"):
            update_resource(row["id"], is_official=not bool(row.get("is_official")))
            st.rerun()
        if e3.button("Delete resource"):
            delete_resource(row["id"])
            st.rerun()
        with st.form("res_edit"):
            nt = st.text_input("Edit title", value=row["title"])
            nu = st.text_input("Edit URL", value=row.get("url") or "")
            nd = st.text_input("Edit description", value=row.get("description") or "")
            if st.form_submit_button("Save resource"):
                update_resource(row["id"], title=nt, url=nu, description=nd)
                st.success("Saved.")
                st.rerun()

with tab_flags:
    section_header("Feature flags (view / toggle)")
    flags = get_feature_flags()
    if not flags:
        empty_state("No flags", "Seeded on init_db.")
    else:
        st.dataframe(pd.DataFrame(flags), use_container_width=True, hide_index=True)
        for fl in flags:
            on = bool(fl.get("enabled"))
            cols = st.columns((4, 1))
            cols[0].markdown(
                f"{'🟢' if on else '⚪'} **{fl["key"]}** — {fl.get("description") or ''}"
            )
            if cols[1].button("Off" if on else "On", key=f"flag_tog_{fl['key']}"):
                set_feature_flag(fl["key"], not on)
                st.rerun()

with tab_ex:
    section_header("Seed DEMO exchanges")
    st.caption("Idempotent seed of labelled DEMO rows into `exchanges`. Never invents real referral URLs.")
    if st.button("Run seed_demo_exchanges", type="primary"):
        n = seed_demo_exchanges()
        st.success(f"Inserted {n} new DEMO exchange row(s) (0 means already seeded).")
    st.page_link("pages/20_Exchange_Directory.py", label="Open Exchange Directory admin UI", icon="🏦")
    st.page_link("pages/12_Admin_Partner_Links.py", label="Open Partner Links admin", icon="🔗")

with tab_sub:
    section_header("Subscriptions")
    sub = get_or_create_free()
    st.info(
        "**Coming Soon** — PRO subscriptions are architecture-only. "
        "No Stripe/checkout. No charges. Local tier stub only. "
        + PRO_PAYMENTS_MESSAGE
    )
    st.json({"tier": sub.get("tier"), "status": sub.get("status"), "id": sub.get("id")})
    st.caption("Use Account / PRO pages + MCCC_PRO_UNLOCK=1 for local UI unlocks.")

if tab_diag is not None:
    with tab_diag:
        section_header("Diagnostics (MCCC_DEV)", f"v{__version__} — no secrets")
        st.caption("Same data as pages/23_Diagnostics.py. Secrets never shown.")
        status = config_status_public()
        st.json(
            {
                "version": __version__,
                "warnings": status.get("warnings"),
                "optional_keys": status.get("optional_keys"),
                "mccc_pro_unlock": status.get("mccc_pro_unlock"),
                "bootstrap_admin_email_set": status.get("bootstrap_admin_email_set"),
            }
        )
        flags = get_feature_flags()
        st.dataframe(
            [{"key": f["key"], "enabled": bool(f["enabled"])} for f in flags],
            use_container_width=True,
            hide_index=True,
        )
        st.page_link("pages/23_Diagnostics.py", label="Open full Diagnostics page", icon="🩺")

footer("Admin")
