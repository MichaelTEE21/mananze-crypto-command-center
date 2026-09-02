"""Announcements CRUD — create / publish / expire / list for Command Center + Admin."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now


def list_published(
    limit: int = 10,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Return published announcements that are not expired.

    expires_at empty/NULL = never expires. Comparison is lexicographic ISO UTC
    (same format as utc_now()).
    """
    now = utc_now()
    lim = max(1, min(int(limit or 10), 100))
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM announcements
            WHERE published = 1
              AND (
                expires_at IS NULL
                OR expires_at = ''
                OR expires_at > ?
              )
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (now, lim),
        ).fetchall()
        return [dict(r) for r in rows]


def list_all(db_path: Optional[Path] = None, limit: int = 100) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit or 100), 500))
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM announcements ORDER BY created_at DESC, id DESC LIMIT ?",
            (lim,),
        ).fetchall()
        return [dict(r) for r in rows]


def get(announcement_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM announcements WHERE id=?", (int(announcement_id),)
        ).fetchone()
        return dict(row) if row else None


def create(
    title: str,
    body: str = "",
    published: bool = True,
    expires_at: str = "",
    db_path: Optional[Path] = None,
) -> int:
    """Insert announcement. Returns id."""
    title_n = (title or "").strip()
    if not title_n:
        raise ValueError("title is required")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO announcements (title, body, published, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (title_n, body or "", 1 if published else 0, expires_at or "", now),
        )
        return int(cur.lastrowid)


def update(
    announcement_id: int,
    *,
    title: Optional[str] = None,
    body: Optional[str] = None,
    published: Optional[bool] = None,
    expires_at: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> None:
    fields: dict[str, Any] = {}
    if title is not None:
        t = title.strip()
        if not t:
            raise ValueError("title is required")
        fields["title"] = t
    if body is not None:
        fields["body"] = body
    if published is not None:
        fields["published"] = 1 if published else 0
    if expires_at is not None:
        fields["expires_at"] = expires_at
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [int(announcement_id)]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE announcements SET {cols} WHERE id=?", vals)


def publish(announcement_id: int, published: bool = True, db_path: Optional[Path] = None) -> None:
    update(announcement_id, published=published, db_path=db_path)


def expire(announcement_id: int, expires_at: Optional[str] = None, db_path: Optional[Path] = None) -> None:
    """Set expires_at to now (or provided ISO) so list_published hides it."""
    update(announcement_id, expires_at=expires_at if expires_at is not None else utc_now(), db_path=db_path)


def delete(announcement_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM announcements WHERE id=?", (int(announcement_id),))
