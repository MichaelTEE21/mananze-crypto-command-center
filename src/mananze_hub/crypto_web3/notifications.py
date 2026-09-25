"""In-app notifications CRUD. user_id optional for local-single-user mode."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now


def create(
    title: str,
    body: str = "",
    category: str = "general",
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> int:
    title_n = (title or "").strip()
    if not title_n:
        raise ValueError("title is required")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO notifications (user_id, title, body, category, read, created_at)
               VALUES (?, ?, ?, ?, 0, ?)""",
            (user_id, title_n, body or "", category or "general", now),
        )
        return int(cur.lastrowid)


def list_notifications(
    user_id: Optional[int] = None,
    unread_only: bool = False,
    category: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        clauses.append("(user_id=? OR user_id IS NULL)")
        params.append(user_id)
    if unread_only:
        clauses.append("read=0")
    if category:
        clauses.append("category=?")
        params.append(category)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM notifications{where} ORDER BY created_at DESC, id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def unread_count(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> int:
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM notifications WHERE read=0"
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM notifications WHERE read=0 AND (user_id=? OR user_id IS NULL)",
                (user_id,),
            ).fetchone()
        return int(row["c"] if row else 0)


def mark_read(notification_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("UPDATE notifications SET read=1 WHERE id=?", (notification_id,))


def mark_unread(notification_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("UPDATE notifications SET read=0 WHERE id=?", (notification_id,))


def mark_all_read(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        if user_id is None:
            conn.execute("UPDATE notifications SET read=1")
        else:
            conn.execute(
                "UPDATE notifications SET read=1 WHERE user_id=? OR user_id IS NULL",
                (user_id,),
            )


def dismiss(notification_id: int, db_path: Optional[Path] = None) -> None:
    """Dismiss = delete the row (gone from inbox)."""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM notifications WHERE id=?", (notification_id,))


def delete(notification_id: int, db_path: Optional[Path] = None) -> None:
    dismiss(notification_id, db_path=db_path)
