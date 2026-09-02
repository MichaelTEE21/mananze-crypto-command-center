"""Research timeline (research_events) + project_tags helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

from mccc.db import connect, utc_now
from mccc.security import reject_sensitive_credential

EVENT_TYPES = ("note", "link", "status_change", "milestone", "risk", "other")


def add_research_event(
    project_id: int,
    body: str = "",
    event_type: str = "note",
    db_path: Optional[Path] = None,
) -> int:
    """Append a timeline event for a project. Rejects credential-like body text."""
    if not project_id:
        raise ValueError("project_id is required")
    et = (event_type or "note").strip().lower() or "note"
    if et not in EVENT_TYPES:
        et = "other"
    reject_sensitive_credential(body or "", field="research_event.body")
    now = utc_now()
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO research_events (project_id, event_type, body, created_at)
               VALUES (?, ?, ?, ?)""",
            (int(project_id), et, body or "", now),
        )
        return int(cur.lastrowid)


def list_research_events(
    project_id: int,
    db_path: Optional[Path] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT * FROM research_events
               WHERE project_id=?
               ORDER BY created_at DESC, id DESC
               LIMIT ?""",
            (int(project_id), int(limit)),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_research_event(event_id: int, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM research_events WHERE id=?", (int(event_id),))


def count_research_events(project_id: Optional[int] = None, db_path: Optional[Path] = None) -> int:
    with connect(db_path) as conn:
        if project_id is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM research_events").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM research_events WHERE project_id=?",
                (int(project_id),),
            ).fetchone()
        return int(row["c"] if row else 0)


def _normalize_tags(tags: Iterable[str] | str) -> list[str]:
    if isinstance(tags, str):
        parts = [p.strip() for p in tags.replace(";", ",").split(",")]
    else:
        parts = [str(p).strip() for p in tags]
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p[:64])
    return out


def list_project_tags(project_id: int, db_path: Optional[Path] = None) -> list[str]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT tag FROM project_tags WHERE project_id=? ORDER BY tag ASC",
            (int(project_id),),
        ).fetchall()
        return [r["tag"] for r in rows]


def set_project_tags(
    project_id: int,
    tags: Iterable[str] | str,
    db_path: Optional[Path] = None,
) -> list[str]:
    """Replace all tags for a project. Returns the normalized tag list."""
    normalized = _normalize_tags(tags)
    now = utc_now()
    with connect(db_path) as conn:
        conn.execute("DELETE FROM project_tags WHERE project_id=?", (int(project_id),))
        for tag in normalized:
            conn.execute(
                """INSERT INTO project_tags (project_id, tag, created_at)
                   VALUES (?, ?, ?)""",
                (int(project_id), tag, now),
            )
    return normalized


def add_project_tag(project_id: int, tag: str, db_path: Optional[Path] = None) -> None:
    tag_n = (tag or "").strip()
    if not tag_n:
        return
    existing = {t.lower() for t in list_project_tags(project_id, db_path=db_path)}
    if tag_n.lower() in existing:
        return
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO project_tags (project_id, tag, created_at)
               VALUES (?, ?, ?)""",
            (int(project_id), tag_n[:64], utc_now()),
        )


def list_all_tags(db_path: Optional[Path] = None) -> list[str]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT tag FROM project_tags ORDER BY tag ASC"
        ).fetchall()
        return [r["tag"] for r in rows]
