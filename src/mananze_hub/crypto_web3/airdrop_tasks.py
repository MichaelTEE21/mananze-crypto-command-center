"""Airdrop task checklist CRUD."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now


def add_task(
    airdrop_id: int,
    title: str,
    notes: str = "",
    done: bool = False,
    db_path: Optional[Path] = None,
) -> int:
    title_n = (title or "").strip()
    if not title_n:
        raise ValueError("title is required")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO airdrop_tasks (airdrop_id, title, done, notes, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (airdrop_id, title_n, 1 if done else 0, notes or "", now),
        )
        return int(cur.lastrowid)


def list_tasks(airdrop_id: int, db_path: Optional[Path] = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM airdrop_tasks WHERE airdrop_id=? ORDER BY id ASC",
            (airdrop_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def toggle_done(task_id: int, done: Optional[bool] = None, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        if done is None:
            row = conn.execute("SELECT done FROM airdrop_tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                return
            done = not bool(row["done"])
        conn.execute("UPDATE airdrop_tasks SET done=? WHERE id=?", (1 if done else 0, task_id))


def delete_task(task_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM airdrop_tasks WHERE id=?", (task_id,))
