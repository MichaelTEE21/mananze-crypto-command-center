"""Education progress CRUD (local SQLite). user_id optional for single-user mode."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now


def upsert_progress(
    lesson_key: str,
    completed: bool = True,
    quiz_score: Optional[float] = None,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> None:
    key = (lesson_key or "").strip()
    if not key:
        raise ValueError("lesson_key is required")
    now = utc_now()
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                "SELECT id FROM education_progress WHERE lesson_key=? AND user_id IS NULL",
                (key,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM education_progress WHERE lesson_key=? AND user_id=?",
                (key, user_id),
            ).fetchone()
        if row:
            conn.execute(
                """UPDATE education_progress
                   SET completed=?, quiz_score=?, updated_at=? WHERE id=?""",
                (1 if completed else 0, quiz_score, now, row["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO education_progress
                   (user_id, lesson_key, completed, quiz_score, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, key, 1 if completed else 0, quiz_score, now),
            )


def list_progress(
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT * FROM education_progress ORDER BY updated_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM education_progress
                   WHERE user_id=? OR user_id IS NULL
                   ORDER BY updated_at DESC""",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_progress(
    lesson_key: str,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    key = (lesson_key or "").strip()
    with connect(db_path) as conn:
        if user_id is None:
            row = conn.execute(
                "SELECT * FROM education_progress WHERE lesson_key=? AND user_id IS NULL",
                (key,),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT * FROM education_progress
                   WHERE lesson_key=? AND (user_id=? OR user_id IS NULL)
                   ORDER BY user_id DESC LIMIT 1""",
                (key, user_id),
            ).fetchone()
        return dict(row) if row else None


def completed_keys(user_id: Optional[int] = None, db_path: Optional[Path] = None) -> set[str]:
    return {r["lesson_key"] for r in list_progress(user_id=user_id, db_path=db_path) if r.get("completed")}
