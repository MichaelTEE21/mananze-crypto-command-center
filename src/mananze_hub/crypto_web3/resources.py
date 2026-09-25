"""Resources directory CRUD — optional project_id, official flag, click_count."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

RESOURCE_TYPES = (
    "docs",
    "explorer",
    "github",
    "twitter",
    "discord",
    "website",
    "audit",
    "article",
    "tool",
    "other",
)


def list_resources(
    project_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    q: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if project_id is not None:
        clauses.append("project_id = ?")
        params.append(int(project_id))
    if resource_type:
        clauses.append("resource_type = ?")
        params.append(resource_type)
    if q:
        clauses.append("(LOWER(title) LIKE ? OR LOWER(url) LIKE ? OR LOWER(description) LIKE ?)")
        needle = f"%{q.strip().lower()}%"
        params.extend([needle, needle, needle])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM resources{where} ORDER BY created_at DESC, id DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_resource(resource_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM resources WHERE id=?", (int(resource_id),)).fetchone()
        return dict(row) if row else None


def add_resource(
    title: str,
    url: str = "",
    resource_type: str = "other",
    project_id: Optional[int] = None,
    description: str = "",
    is_official: bool = False,
    db_path: Optional[Path] = None,
) -> int:
    title_n = (title or "").strip()
    if not title_n:
        raise ValueError("title is required")
    rtype = (resource_type or "other").strip().lower() or "other"
    if rtype not in RESOURCE_TYPES:
        rtype = "other"
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO resources
               (title, url, resource_type, project_id, description, is_official, click_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
            (
                title_n,
                (url or "").strip(),
                rtype,
                int(project_id) if project_id is not None else None,
                description or "",
                1 if is_official else 0,
                now,
            ),
        )
        return int(cur.lastrowid)


def update_resource(resource_id: int, **fields: Any) -> None:
    db_path = fields.pop("db_path", None)
    allowed = {
        "title",
        "url",
        "resource_type",
        "project_id",
        "description",
        "is_official",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "title" in updates:
        updates["title"] = (updates["title"] or "").strip()
        if not updates["title"]:
            raise ValueError("title is required")
    if "resource_type" in updates:
        rt = (updates["resource_type"] or "other").strip().lower() or "other"
        updates["resource_type"] = rt if rt in RESOURCE_TYPES else "other"
    if "is_official" in updates:
        updates["is_official"] = 1 if updates["is_official"] else 0
    if "url" in updates:
        updates["url"] = (updates["url"] or "").strip()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [int(resource_id)]
    with connect(db_path) as conn:
        conn.execute(f"UPDATE resources SET {cols} WHERE id=?", vals)


def delete_resource(resource_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM resources WHERE id=?", (int(resource_id),))


def record_resource_click(resource_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE resources SET click_count = click_count + 1 WHERE id=?",
            (int(resource_id),),
        )


def search_resources(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    rows = list_resources(q=q, db_path=db_path)
    return rows[: max(1, min(int(limit or 25), 100))]
