"""CRUD/smoke tests for exchanges, research events, bookmarks, stage maps, note security."""
from __future__ import annotations

import pytest

from mccc.bookmarks import favourite_refs, is_favourite, set_favourite, toggle_favourite
from mccc.db import (
    AIRDROP_STATUSES,
    PROJECT_STAGES,
    add_airdrop,
    add_project,
    init_db,
    list_airdrops,
    list_projects,
    normalize_airdrop_status,
    normalize_project_stage,
    update_project,
)
from mccc.exchanges import (
    add_exchange,
    delete_exchange,
    list_exchanges,
    resolve_visit_url,
    seed_demo_exchanges,
    update_exchange,
)
from mccc.research import (
    add_research_event,
    delete_research_event,
    list_project_tags,
    list_research_events,
    set_project_tags,
)
from mccc.security import SensitiveCredentialError, reject_sensitive_credential


TWELVE = " ".join(
    [
        "abandon", "ability", "able", "about", "above", "absent",
        "absorb", "abstract", "absurd", "abuse", "access", "accident",
    ]
)


def test_project_stages_canonical():
    assert "WATCHLIST" in PROJECT_STAGES
    assert "WAITING FOR TGE" in PROJECT_STAGES
    assert "ARCHIVED" in PROJECT_STAGES
    assert normalize_project_stage("Monitoring") == "WATCHLIST"
    assert normalize_project_stage("TGE Soon") == "WAITING FOR TGE"
    assert normalize_project_stage("Researching") == "RESEARCHING"
    assert normalize_project_stage(None, "watching") == "WATCHLIST"


def test_airdrop_statuses_canonical(db_path):
    assert "ACTIVE" in AIRDROP_STATUSES
    assert "MISSED" in AIRDROP_STATUSES
    assert normalize_airdrop_status("Farming") == "ACTIVE"
    assert normalize_airdrop_status("Claim Available") == "ACTIVE"
    assert normalize_airdrop_status("Dead") == "MISSED"
    aid = add_airdrop("Map Me", "base", "watching", db_path=db_path)
    hit = next(a for a in list_airdrops(db_path) if a["id"] == aid)
    assert hit["status"] == "DISCOVERED"


def test_stage_migration_on_init(db_path):
    projects = list_projects(db_path)
    assert projects
    for p in projects:
        assert p["stage"] in PROJECT_STAGES
    for a in list_airdrops(db_path):
        assert a["status"] in AIRDROP_STATUSES


def test_exchanges_seed_and_resolve(db_path):
    # init_db already seeds; seed again is idempotent
    assert seed_demo_exchanges(db_path=db_path) == 0
    rows = list_exchanges(db_path=db_path)
    assert len(rows) >= 3
    assert any("DEMO" in r["name"].upper() for r in rows)
    with_ref = next(r for r in rows if (r.get("referral_url") or "").strip())
    assert resolve_visit_url(with_ref) == with_ref["referral_url"].strip()
    official_only = next(r for r in rows if not (r.get("referral_url") or "").strip())
    assert resolve_visit_url(official_only) == official_only["official_url"].strip()


def test_exchanges_crud(db_path):
    eid = add_exchange(
        "Temp DEX",
        type_="DEX",
        official_url="https://example.com/tmp-dex",
        referral_url="",
        db_path=db_path,
    )
    assert eid > 0
    update_exchange(eid, description="updated", referral_url="https://example.com/ref/tmp", db_path=db_path)
    hit = next(e for e in list_exchanges(db_path=db_path) if e["id"] == eid)
    assert hit["description"] == "updated"
    assert resolve_visit_url(hit).endswith("/ref/tmp")
    delete_exchange(eid, db_path=db_path)
    assert all(e["id"] != eid for e in list_exchanges(db_path=db_path))


def test_research_events_crud_and_security(db_path):
    pid = add_project("Timeline Case", "ethereum", stage="RESEARCHING", db_path=db_path)
    eid = add_research_event(pid, body="Read docs", event_type="note", db_path=db_path)
    assert eid > 0
    events = list_research_events(pid, db_path=db_path)
    assert any(e["id"] == eid for e in events)
    with pytest.raises(SensitiveCredentialError):
        add_research_event(pid, body=TWELVE, event_type="note", db_path=db_path)
    with pytest.raises(SensitiveCredentialError):
        reject_sensitive_credential("my private key backup", field="notes")
    delete_research_event(eid, db_path=db_path)
    assert all(e["id"] != eid for e in list_research_events(pid, db_path=db_path))


def test_project_tags_and_favourites(db_path):
    pid = add_project("Tagged", "solana", stage="DISCOVERED", db_path=db_path)
    tags = set_project_tags(pid, "defi, L2, DeFi", db_path=db_path)
    assert tags == ["defi", "L2"] or set(tags) == {"defi", "L2"}
    assert "defi" in list_project_tags(pid, db_path=db_path)
    assert not is_favourite("project", str(pid), db_path=db_path)
    set_favourite("project", str(pid), favourite=True, db_path=db_path)
    assert is_favourite("project", str(pid), db_path=db_path)
    assert str(pid) in favourite_refs("project", db_path=db_path)
    assert toggle_favourite("project", str(pid), db_path=db_path) is False


def test_project_rich_fields(db_path):
    pid = add_project(
        "Rich",
        "ethereum",
        stage="FARMING",
        ticker="RICH",
        twitter="https://example.com/x",
        research_notes="ok notes",
        personal_rating=4,
        db_path=db_path,
    )
    update_project(pid, github="https://example.com/gh", risk_notes="bridge risk", db_path=db_path)
    hit = next(p for p in list_projects(db_path) if p["id"] == pid)
    assert hit["ticker"] == "RICH"
    assert hit["personal_rating"] == 4
    assert hit["github"] == "https://example.com/gh"
    assert hit["stage"] == "FARMING"
