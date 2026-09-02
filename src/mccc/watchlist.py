"""Watchlist + alerts CRUD (local SQLite). user_id optional for single-user mode."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

ITEM_TYPES = ("token", "project", "wallet")


def add_item(
    symbol_or_ref: str,
    item_type: str = "token",
    notes: str = "",
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> int:
    ref = (symbol_or_ref or "").strip()
    if not ref:
        raise ValueError("symbol_or_ref is required")
    itype = (item_type or "token").strip().lower()
    if itype not in ITEM_TYPES:
        raise ValueError(f"item_type must be one of {ITEM_TYPES}")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO watchlist_items (user_id, item_type, symbol_or_ref, notes, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, itype, ref, notes or "", now),
        )
        return int(cur.lastrowid)


def list_items(
    user_id: Optional[int] = None,
    item_type: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        clauses.append("(user_id=? OR user_id IS NULL)")
        params.append(user_id)
    if item_type:
        clauses.append("item_type=?")
        params.append(item_type)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM watchlist_items{where} ORDER BY created_at DESC, id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_item(item_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM watchlist_items WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None


def update_item(item_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {"symbol_or_ref", "item_type", "notes", "user_id"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "item_type" in updates and updates["item_type"] not in ITEM_TYPES:
        raise ValueError(f"item_type must be one of {ITEM_TYPES}")
    if not updates:
        return
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [item_id]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE watchlist_items SET {cols} WHERE id=?", vals)


def delete_item(item_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM alerts WHERE watchlist_id=?", (item_id,))
        conn.execute("DELETE FROM watchlist_items WHERE id=?", (item_id,))


def add_alert(
    alert_type: str,
    threshold: Optional[float] = None,
    watchlist_id: Optional[int] = None,
    meta: str = "",
    user_id: Optional[int] = None,
    active: int = 1,
    db_path: Optional[Path] = None,
) -> int:
    atype = (alert_type or "price").strip()
    if not atype:
        raise ValueError("alert_type is required")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO alerts
               (user_id, watchlist_id, alert_type, threshold, meta, active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, watchlist_id, atype, threshold, meta or "", 1 if active else 0, now),
        )
        return int(cur.lastrowid)


def list_alerts(
    user_id: Optional[int] = None,
    active_only: bool = False,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        clauses.append("(user_id=? OR user_id IS NULL)")
        params.append(user_id)
    if active_only:
        clauses.append("active=1")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM alerts{where} ORDER BY created_at DESC, id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def set_alert_active(alert_id: int, active: bool, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("UPDATE alerts SET active=? WHERE id=?", (1 if active else 0, alert_id))


def delete_alert(alert_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
