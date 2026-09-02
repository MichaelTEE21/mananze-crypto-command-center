"""Portfolio — full CRUD + PnL + CSV via portfolio.py + market prices."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import streamlit as st

from mccc.market_provider import get_default_provider
from mccc.portfolio import (
    add_asset,
    compute_summary,
    delete_asset,
    export_csv,
    import_csv,
    list_assets,
    update_asset,
)
from mccc.ui import (
    footer,
    demo_callout,
    empty_state,
    error_banner,
    hero,
    live_or_demo_badge,
    metric_card,
    page_setup,
    session_user_id,
)

page_setup("portfolio", "Portfolio")
hero("Portfolio", "Local holdings book — cost basis, PnL, CSV. Never treated as exchange sync.")

uid = session_user_id()
provider = get_default_provider()

st.subheader("Add asset")
with st.form("add_asset", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    symbol = c1.text_input("Symbol", placeholder="BTC")
    quantity = c2.number_input("Quantity", min_value=0.0, value=0.0, format="%.8f")
    purchase_price = c3.number_input("Purchase price (USD)", min_value=0.0, value=0.0, format="%.8f")
    network = c4.text_input("Network", placeholder="ethereum")
    name = st.text_input("Name (optional)", placeholder="Bitcoin")
    c5, c6 = st.columns(2)
    purchase_date = c5.text_input("Purchase date", placeholder="YYYY-MM-DD")
    notes = c6.text_input("Notes")
    if st.form_submit_button("Add to portfolio", type="primary"):
        try:
            add_asset(
                symbol=symbol,
                quantity=quantity,
                purchase_price=purchase_price,
                name=name,
                purchase_date=purchase_date,
                network=network,
                notes=notes,
                user_id=uid,
            )
            st.success("Asset saved.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            error_banner(str(exc))

assets = list_assets(user_id=uid)
price_map, px_source, px_live = provider.price_map()
summary = compute_summary(assets, price_map, is_live=px_live)

st.subheader("Summary")
live_or_demo_badge(summary["is_live"])
st.caption(f"{summary['source_note']} · {px_source}")
if not summary["is_live"]:
    demo_callout("PnL uses DEMO or incomplete prices when live feed is unavailable.")

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card(f"${summary['total_value']:,.2f}", "Total value")
with m2:
    metric_card(f"${summary['total_cost']:,.2f}", "Cost basis")
with m3:
    metric_card(f"${summary['total_pnl']:,.2f}", "Unrealized PnL")
with m4:
    metric_card(str(len(assets)), f"Assets · {summary['unpriced_count']} unpriced")

if not assets:
    empty_state("Portfolio empty", "Add an asset above or import a CSV.")
else:
    pos = summary["positions"]
    view = []
    for p in pos:
        view.append(
            {
                "ID": p["id"],
                "Symbol": p["symbol"],
                "Name": p.get("name") or "",
                "Qty": p["quantity"],
                "Cost/unit": p.get("purchase_price"),
                "Cost": p.get("cost"),
                "Price": p.get("current_price"),
                "Value": p.get("value"),
                "PnL": p.get("pnl"),
                "PnL %": p.get("pnl_pct"),
                "Alloc %": p.get("allocation"),
                "Network": p.get("network") or "",
            }
        )
    st.dataframe(pd.DataFrame(view), use_container_width=True, hide_index=True)

    st.subheader("Edit / delete")
    ids = {f"#{a['id']} {a['symbol']}": a["id"] for a in assets}
    pick = st.selectbox("Select asset", list(ids.keys()))
    aid = ids[pick]
    cur = next(a for a in assets if a["id"] == aid)
    with st.form("edit_asset"):
        symbol = st.text_input("Symbol", value=cur["symbol"])
        quantity = st.number_input("Quantity", min_value=0.0, value=float(cur["quantity"]), format="%.8f")
        purchase_price = st.number_input(
            "Purchase price", min_value=0.0, value=float(cur["purchase_price"] or 0), format="%.8f"
        )
        name = st.text_input("Name", value=cur.get("name") or "")
        network = st.text_input("Network", value=cur.get("network") or "")
        notes = st.text_input("Notes", value=cur.get("notes") or "")
        purchase_date = st.text_input("Purchase date", value=cur.get("purchase_date") or "")
        a, b = st.columns(2)
        if a.form_submit_button("Save", type="primary"):
            update_asset(
                aid,
                symbol=symbol,
                quantity=quantity,
                purchase_price=purchase_price,
                name=name,
                network=network,
                notes=notes,
                purchase_date=purchase_date,
            )
            st.success("Updated.")
            st.rerun()
        if b.form_submit_button("Delete"):
            delete_asset(aid)
            st.warning("Deleted.")
            st.rerun()

st.divider()
st.subheader("CSV import / export")
st.download_button(
    "Download CSV",
    data=export_csv(assets),
    file_name="mccc_portfolio.csv",
    mime="text/csv",
    disabled=not assets,
)
uploaded = st.file_uploader("Import CSV", type=["csv"])
if uploaded and st.button("Import rows", type="primary"):
    text = uploaded.read().decode("utf-8", errors="replace")
    try:
        ids_created = import_csv(text, user_id=uid)
        st.success(f"Imported {len(ids_created)} row(s).")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        error_banner(str(exc))

footer("Portfolio")
