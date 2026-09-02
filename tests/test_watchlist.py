"""Watchlist + alerts CRUD tests."""
from __future__ import annotations

import pytest

from mccc.watchlist import (
    add_alert,
    add_item,
    delete_alert,
    delete_item,
    list_alerts,
    list_items,
    set_alert_active,
    update_item,
)


def test_watchlist_crud(db_path):
    wid = add_item("BTC", item_type="token", notes="watch", db_path=db_path)
    assert wid > 0
    items = list_items(db_path=db_path)
    assert any(i["id"] == wid and i["symbol_or_ref"] == "BTC" for i in items)
    update_item(wid, notes="updated", db_path=db_path)
    hit = next(i for i in list_items(db_path=db_path) if i["id"] == wid)
    assert hit["notes"] == "updated"
    delete_item(wid, db_path=db_path)
    assert all(i["id"] != wid for i in list_items(db_path=db_path))


def test_item_type_validation(db_path):
    with pytest.raises(ValueError):
        add_item("x", item_type="invalid", db_path=db_path)
    add_item("0xabc", item_type="wallet", db_path=db_path)
    add_item("Demo Project", item_type="project", db_path=db_path)
    types = {i["item_type"] for i in list_items(db_path=db_path)}
    assert "wallet" in types and "project" in types


def test_alerts(db_path):
    wid = add_item("ETH", db_path=db_path)
    aid = add_alert("price", threshold=3000.0, watchlist_id=wid, db_path=db_path)
    assert aid > 0
    alerts = list_alerts(db_path=db_path)
    assert any(a["id"] == aid and a["active"] == 1 for a in alerts)
    set_alert_active(aid, False, db_path=db_path)
    assert list_alerts(active_only=True, db_path=db_path) == []
    delete_alert(aid, db_path=db_path)
    assert all(a["id"] != aid for a in list_alerts(db_path=db_path))
