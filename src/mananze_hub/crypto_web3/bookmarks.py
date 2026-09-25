"""Bookmarks / favourites — projects, tokens, wallets, resources, lessons, …"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

ITEM_TYPES = (
    "project",
    "airdrop",
    "token",
    "wallet",
    "resource",
    "lesson",
    "exchange",
    "note",
    "intelligence_event",
    "narrative",
    "other",
)


def get_bookmark(
    item_type: str,
    item_ref: str,
    db_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM bookmarks WHERE item_type=? AND item_ref=? LIMIT 1",
            (item_type, str(item_ref)),
        ).fetchone()
        return dict(row) if row else None


def is_favourite(
    item_type: str,
    item_ref: str,
    db_path: Optional[Path] = None,
) -> bool:
    row = get_bookmark(item_type, item_ref, db_path=db_path)
    return bool(row and row.get("favourite"))


def set_favourite(
    item_type: str,
    item_ref: str,
    favourite: bool = True,
    notes: str = "",
    tags: str = "",
    priority: int = 3,
    db_path: Optional[Path] = None,
) -> int:
    """Upsert a bookmark and set favourite flag. Returns bookmark id."""
    ref = str(item_ref)
    itype = (item_type or "other").strip().lower() or "other"
    existing = get_bookmark(itype, ref, db_path=db_path)
    now = utc_now()
    with connect(db_path) as conn:
        if existing:
            conn.execute(
                """UPDATE bookmarks
                   SET favourite=?, notes=?, tags=?, priority=?
                   WHERE id=?""",
                (
                    1 if favourite else 0,
                    notes if notes != "" else (existing.get("notes") or ""),
                    tags if tags != "" else (existing.get("tags") or ""),
                    int(priority),
                    existing["id"],
                ),
            )
            return int(existing["id"])
        cur = conn.execute(
            """INSERT INTO bookmarks (item_type, item_ref, notes, tags, priority, favourite, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (itype, ref, notes or "", tags or "", int(priority), 1 if favourite else 0, now),
        )
        return int(cur.lastrowid)


def toggle_favourite(
    item_type: str,
    item_ref: str,
    db_path: Optional[Path] = None,
) -> bool:
    """Toggle favourite; returns new favourite state."""
    current = is_favourite(item_type, item_ref, db_path=db_path)
    set_favourite(item_type, item_ref, favourite=not current, db_path=db_path)
    return not current


def list_bookmarks(
    item_type: Optional[str] = None,
    favourites_only: bool = False,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if item_type:
        clauses.append("item_type = ?")
        params.append(item_type)
    if favourites_only:
        clauses.append("favourite = 1")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM bookmarks{where} ORDER BY priority ASC, created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def list_favourites(
    item_type: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    return list_bookmarks(item_type=item_type, favourites_only=True, db_path=db_path)


def favourite_refs(item_type: str, db_path: Optional[Path] = None) -> set[str]:
    return {b["item_ref"] for b in list_favourites(item_type=item_type, db_path=db_path)}


def delete_bookmark(
    bookmark_id: Optional[int] = None,
    *,
    item_type: Optional[str] = None,
    item_ref: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> None:
    with connect(db_path) as conn:
        if bookmark_id is not None:
            conn.execute("DELETE FROM bookmarks WHERE id=?", (int(bookmark_id),))
            return
        if item_type and item_ref is not None:
            conn.execute(
                "DELETE FROM bookmarks WHERE item_type=? AND item_ref=?",
                (item_type, str(item_ref)),
            )
