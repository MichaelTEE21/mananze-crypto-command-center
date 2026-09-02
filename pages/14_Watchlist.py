"""Watchlist + alerts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.subscriptions import has_pro_feature
from mccc.market_provider import get_default_provider
from mccc.notifications import create as create_notification
from mccc.ui import empty_state, error_banner, footer, hero, page_setup, pro_locked_panel, session_user_id, upgrade_cta
from mccc.bookmarks import ITEM_TYPES, delete_bookmark, list_bookmarks, set_favourite
from mccc.watchlist import (
    ITEM_TYPES,
    add_alert,
    add_item,
    delete_alert,
    delete_item,
    list_alerts,
    list_items,
    set_alert_active,
)

page_setup("watchlist", "Watchlist")
hero("Watchlist", "Tokens, projects, and wallets to monitor — plus local price alerts.")

uid = session_user_id()

st.subheader("Add item")
with st.form("add_watch", clear_on_submit=True):
    c1, c2 = st.columns(2)
    ref = c1.text_input("Symbol or ref", placeholder="ETH / project name / 0x…")
    itype = c2.selectbox("Type", list(ITEM_TYPES))
    notes = st.text_input("Notes")
    if st.form_submit_button("Add", type="primary"):
        try:
            add_item(ref, item_type=itype, notes=notes, user_id=uid)
            st.success("Added.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

items = list_items(user_id=uid)
st.subheader(f"Items ({len(items)})")
if not items:
    empty_state("Watchlist empty", "Add a token, project, or wallet ref above.")
else:
    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
    ids = {f"#{i['id']} [{i['item_type']}] {i['symbol_or_ref']}": i["id"] for i in items}
    pick = st.selectbox("Remove item", list(ids.keys()))
    if st.button("Delete selected item"):
        delete_item(ids[pick])
        st.warning("Removed.")
        st.rerun()

st.divider()
st.subheader("Alerts")
if not has_pro_feature("pro_wallet_alerts", user_id=uid):
    pro_locked_panel("Watchlist alerts")
    upgrade_cta("Unlimited/advanced alerts are a PRO architecture feature.")
    st.caption("You can still create alerts locally for architecture testing.")

with st.form("add_alert", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    atype = c1.selectbox("Alert type", ["price_above", "price_below", "custom"])
    threshold = c2.number_input("Threshold (USD)", min_value=0.0, value=0.0)
    wl_opts = {"— none —": None}
    for i in items:
        wl_opts[f"#{i['id']} {i['symbol_or_ref']}"] = i["id"]
    wl_pick = c3.selectbox("Watchlist item", list(wl_opts.keys()))
    meta = st.text_input("Meta / note")
    if st.form_submit_button("Create alert", type="primary"):
        try:
            add_alert(
                alert_type=atype,
                threshold=threshold,
                watchlist_id=wl_opts[wl_pick],
                meta=meta,
                user_id=uid,
            )
            st.success("Alert saved.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

alerts = list_alerts(user_id=uid)
if not alerts:
    empty_state("No alerts", "Create a threshold alert above.")
else:
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
    for al in alerts:
        cols = st.columns((4, 1, 1))
        cols[0].caption(f"#{al['id']} {al['alert_type']} @ {al.get('threshold')} · active={al['active']}")
        if cols[1].button("Toggle", key=f"tog_al_{al['id']}"):
            set_alert_active(al["id"], not bool(al["active"]))
            st.rerun()
        if cols[2].button("Delete", key=f"del_al_{al['id']}"):
            delete_alert(al["id"])
            st.rerun()

st.divider()
st.subheader("Evaluate alerts (local)")
st.caption("Compares active price alerts to current market_provider prices. Labels DEMO vs live.")
if st.button("Run alert check now", type="primary"):
    provider = get_default_provider()
    pmap, source, is_live = provider.price_map()
    fired = 0
    for al in list_alerts(user_id=uid, active_only=True):
        if not al.get("watchlist_id"):
            continue
        item = next((i for i in items if i["id"] == al["watchlist_id"]), None)
        if not item or item.get("item_type") != "token":
            continue
        sym = str(item["symbol_or_ref"]).upper()
        px = pmap.get(sym)
        thr = al.get("threshold")
        if px is None or thr is None:
            continue
        hit = False
        if al["alert_type"] == "price_above" and px >= float(thr):
            hit = True
        if al["alert_type"] == "price_below" and px <= float(thr):
            hit = True
        if hit:
            tag = "LIVE" if is_live else "DEMO"
            create_notification(
                title=f"Alert [{tag}] {sym} {al['alert_type']}",
                body=f"{sym} at {px} vs threshold {thr}. Source: {source}",
                category="alert",
                user_id=uid,
            )
            fired += 1
    st.success(f"Fired {fired} notification(s). Source: {source} · live={is_live}")

st.divider()
st.subheader("Bookmarks")
st.caption("Favourites via bookmarks.py — projects, tokens, wallets, resources, lessons, notes.")
with st.form("add_bookmark", clear_on_submit=True):
    bc1, bc2 = st.columns(2)
    b_ref = bc1.text_input("Item ref", placeholder="project id / ETH / lesson key")
    b_type = bc2.selectbox("Bookmark type", list(ITEM_TYPES))
    b_notes = st.text_input("Bookmark notes")
    b_tags = st.text_input("Tags")
    b_pri = st.slider("Priority (1=high)", 1, 5, 3)
    if st.form_submit_button("Save bookmark", type="primary"):
        try:
            set_favourite(b_type, b_ref, favourite=True, notes=b_notes, tags=b_tags, priority=b_pri)
            st.success("Bookmarked.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

bmarks = list_bookmarks()
if not bmarks:
    empty_state("No bookmarks", "Star items from Education / Research or add above.")
else:
    type_f = st.selectbox("Filter bookmarks", ["(all)"] + list(ITEM_TYPES), key="bm_filter")
    shown = [b for b in bmarks if type_f == "(all)" or b.get("item_type") == type_f]
    cols = ["id", "item_type", "item_ref", "favourite", "priority", "tags", "notes", "created_at"]
    df_bm = pd.DataFrame(shown)
    st.dataframe(df_bm[[c for c in cols if c in df_bm.columns]], use_container_width=True, hide_index=True)
    if shown:
        labels = {f"#{b['id']} [{b['item_type']}] {b['item_ref']}": b["id"] for b in shown}
        pick_bm = st.selectbox("Remove bookmark", list(labels.keys()), key="bm_del")
        if st.button("Delete bookmark"):
            delete_bookmark(labels[pick_bm])
            st.warning("Bookmark removed.")
            st.rerun()

footer("Watchlist")
