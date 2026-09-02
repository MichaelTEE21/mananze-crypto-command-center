"""Pure search helpers across local MCCC entities (no Streamlit)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

from mccc.db import list_airdrops, list_notes, list_projects, list_wallets
from mccc.exchanges import list_exchanges
from mccc.paths import EDUCATION_DIR, ensure_dirs
from mccc.resources import list_resources

SEARCH_CATEGORIES = (
    "projects",
    "airdrops",
    "wallets",
    "exchanges",
    "education",
    "resources",
    "notes",
)


def _haystack(row: dict[str, Any], keys: Iterable[str] | None = None) -> str:
    if keys is None:
        return " ".join(str(v) for v in row.values() if v is not None).lower()
    parts = []
    for k in keys:
        v = row.get(k)
        if v is not None:
            parts.append(str(v))
    return " ".join(parts).lower()


def match_query(haystack: str, q: str) -> bool:
    """Case-insensitive substring match; empty query matches nothing."""
    needle = (q or "").strip().lower()
    if not needle:
        return False
    return needle in (haystack or "").lower()


def search_projects(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    hits = [
        p
        for p in list_projects(db_path=db_path)
        if match_query(_haystack(p, ("name", "chain", "stage", "status", "notes", "ticker", "risk_notes", "research_notes")), q)
    ]
    return hits[:limit]


def search_airdrops(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    hits = [
        a
        for a in list_airdrops(db_path=db_path)
        if match_query(
            _haystack(a, ("project_name", "chain", "status", "notes", "token", "official_website", "claim_page")),
            q,
        )
    ]
    return hits[:limit]


def search_wallets(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    hits = [
        w
        for w in list_wallets(db_path=db_path)
        if match_query(_haystack(w, ("label", "address", "chain", "notes")), q)
    ]
    return hits[:limit]


def search_exchanges(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    hits = [
        e
        for e in list_exchanges(db_path=db_path)
        if match_query(
            _haystack(e, ("name", "type", "region", "description", "chains", "assets", "security_info")),
            q,
        )
    ]
    return hits[:limit]


def search_education(q: str, education_dir: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    """Return lesson dicts with key, title, path, snippet — not inventing progress."""
    ensure_dirs()
    root = education_dir or EDUCATION_DIR
    needle = (q or "").strip().lower()
    if not needle:
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if needle in path.stem.lower() or needle in text.lower():
            title = path.stem.replace("_", " ").title()
            # Prefer H1 if present
            for line in text.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            out.append(
                {
                    "key": path.stem,
                    "title": title,
                    "path": str(path),
                    "snippet": text[:240].replace("\n", " "),
                }
            )
        if len(out) >= limit:
            break
    return out


def search_resources(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    from mccc.resources import search_resources as _sr

    return _sr(q, db_path=db_path, limit=limit)


def search_notes(q: str, db_path: Optional[Path] = None, limit: int = 25) -> list[dict[str, Any]]:
    hits = [
        n
        for n in list_notes(db_path=db_path)
        if match_query(_haystack(n, ("title", "body", "tags")), q)
    ]
    return hits[:limit]


def search_all(
    q: str,
    categories: Optional[Iterable[str]] = None,
    db_path: Optional[Path] = None,
    limit_per: int = 25,
) -> dict[str, list[dict[str, Any]]]:
    """Run search across selected categories. Returns dict keyed by category."""
    cats = list(categories) if categories else list(SEARCH_CATEGORIES)
    result: dict[str, list[dict[str, Any]]] = {}
    dispatch = {
        "projects": lambda: search_projects(q, db_path=db_path, limit=limit_per),
        "airdrops": lambda: search_airdrops(q, db_path=db_path, limit=limit_per),
        "wallets": lambda: search_wallets(q, db_path=db_path, limit=limit_per),
        "exchanges": lambda: search_exchanges(q, db_path=db_path, limit=limit_per),
        "education": lambda: search_education(q, limit=limit_per),
        "resources": lambda: search_resources(q, db_path=db_path, limit=limit_per),
        "notes": lambda: search_notes(q, db_path=db_path, limit=limit_per),
    }
    for cat in cats:
        if cat in dispatch:
            result[cat] = dispatch[cat]()
    return result
