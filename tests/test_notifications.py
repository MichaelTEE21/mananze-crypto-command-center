"""Notifications CRUD tests."""
from __future__ import annotations

from mccc.notifications import (
    create,
    dismiss,
    list_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)


def test_create_list_mark_dismiss(db_path):
    nid = create("Hello", body="World", category="system", db_path=db_path)
    assert nid > 0
    rows = list_notifications(db_path=db_path)
    assert any(r["id"] == nid and r["read"] == 0 for r in rows)
    assert unread_count(db_path=db_path) >= 1
    mark_read(nid, db_path=db_path)
    hit = next(r for r in list_notifications(db_path=db_path) if r["id"] == nid)
    assert hit["read"] == 1
    dismiss(nid, db_path=db_path)
    assert all(r["id"] != nid for r in list_notifications(db_path=db_path))


def test_mark_all_read(db_path):
    create("A", db_path=db_path)
    create("B", db_path=db_path)
    assert unread_count(db_path=db_path) >= 2
    mark_all_read(db_path=db_path)
    assert unread_count(db_path=db_path) == 0


def test_filter_unread_and_category(db_path):
    create("Alert one", category="alert", db_path=db_path)
    create("Info one", category="info", db_path=db_path)
    unread = list_notifications(unread_only=True, db_path=db_path)
    assert all(r["read"] == 0 for r in unread)
    alerts = list_notifications(category="alert", db_path=db_path)
    assert all(r["category"] == "alert" for r in alerts)
