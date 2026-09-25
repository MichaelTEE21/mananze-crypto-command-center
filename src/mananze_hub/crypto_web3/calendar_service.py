"""Calendar architecture foundation — event types + list helpers over db.calendar_events."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from mccc.db import (
    CALENDAR_EVENT_TYPES,
    add_calendar_event,
    ensure_calendar_schema,
    get_calendar_event,
    list_calendar_events,
    seed_demo_calendar_events,
)

EVENT_TYPE_LABELS = {
    "airdrop": "Airdrops",
    "unlock": "Unlocks",
    "burn": "Burns",
    "project": "Project",
    "governance": "Governance",
    "important": "Important",
}


def ensure_ready(db_path: Optional[Path] = None) -> None:
    ensure_calendar_schema(db_path)
    seed_demo_calendar_events(db_path)


def list_events(
    *,
    event_type: Optional[str] = None,
    month: Optional[str] = None,
    include_demo: bool = True,
    limit: int = 200,
    db_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    ensure_ready(db_path)
    return list_calendar_events(
        event_type=event_type,
        month=month,
        include_demo=include_demo,
        limit=limit,
        db_path=db_path,
    )


def events_for_month(year: int, month: int, **kwargs) -> list[dict[str, Any]]:
    return list_events(month=f"{year:04d}-{month:02d}", **kwargs)


def month_grid(year: int, month: int) -> list[list[Optional[date]]]:
    """Return weeks as lists of date|None for Month view scaffolding."""
    first_weekday, ndays = monthrange(year, month)  # Monday=0
    # Streamlit-friendly Sunday-first optional — keep Monday-first ISO
    weeks: list[list[Optional[date]]] = []
    week: list[Optional[date]] = [None] * first_weekday
    for day in range(1, ndays + 1):
        week.append(date(year, month, day))
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)
    return weeks


def intelligence_hook(event: dict[str, Any]) -> Optional[dict[str, str]]:
    """Click-through hint when entity_ref exists — does not invent links."""
    ref = (event.get("entity_ref") or "").strip()
    et = (event.get("entity_type") or "").strip().lower()
    if not ref:
        return None
    return {
        "intel_report_q": ref,
        "mccc_analyse_entity_hint": et if et in ("token", "wallet", "protocol", "project", "contract", "rwa") else "auto",
    }


def parse_year_month(value: str | None = None) -> tuple[int, int]:
    if value:
        try:
            dt = datetime.strptime(value.strip()[:7], "%Y-%m")
            return dt.year, dt.month
        except ValueError:
            pass
    today = date.today()
    return today.year, today.month


__all__ = [
    "CALENDAR_EVENT_TYPES",
    "EVENT_TYPE_LABELS",
    "add_calendar_event",
    "ensure_ready",
    "events_for_month",
    "get_calendar_event",
    "intelligence_hook",
    "list_events",
    "month_grid",
    "parse_year_month",
    "seed_demo_calendar_events",
]
