"""Core DB helper tests."""
from __future__ import annotations

from mccc.db import (
    add_airdrop,
    add_note,
    add_project,
    add_wallet,
    delete_project,
    get_feature_flags,
    init_db,
    is_feature_enabled,
    list_airdrops,
    list_notes,
    list_projects,
    list_wallets,
    log_event,
    set_feature_flag,
    update_project,
    usage_summary,
)


def test_init_seeds_demo_projects_and_airdrops(db_path):
    projects = list_projects(db_path)
    airdrops = list_airdrops(db_path)
    assert len(projects) >= 3
    assert any("DEMO" in p["name"] for p in projects)
    assert len(airdrops) >= 3
    assert any("DEMO" in a["project_name"] for a in airdrops)


def test_project_crud(db_path):
    pid = add_project("Test Case", "ethereum", "researching", "note", 2, db_path=db_path)
    assert pid > 0
    update_project(pid, status="watching", notes="updated", db_path=db_path)
    rows = list_projects(db_path)
    hit = next(p for p in rows if p["id"] == pid)
    assert hit["status"] == "watching"
    assert hit["notes"] == "updated"
    delete_project(pid, db_path=db_path)
    assert all(p["id"] != pid for p in list_projects(db_path))


def test_airdrop_add(db_path):
    aid = add_airdrop("DEMO X", "base", "watching", "notes", "DEMO / unknown", "", db_path=db_path)
    assert aid > 0
    assert any(a["id"] == aid for a in list_airdrops(db_path))


def test_wallet_public_only(db_path):
    wid = add_wallet("Watch", "0xDEMO000000000000000000000000000000000099", "ethereum", db_path=db_path)
    assert wid > 0
    assert len(list_wallets(db_path)) >= 1


def test_wallet_rejects_seed_marker(db_path):
    import pytest

    with pytest.raises(ValueError):
        add_wallet("Bad", "my seed phrase words here forever", db_path=db_path)


def test_usage_and_flags(db_path):
    log_event("page_view", "command_center", db_path=db_path)
    log_event("case_opened", "project_tracker", meta="x", db_path=db_path)
    summary = usage_summary(db_path)
    assert summary["total_events"] >= 2
    flags = get_feature_flags(db_path)
    assert flags
    key = flags[0]["key"]
    set_feature_flag(key, True, db_path=db_path)
    assert is_feature_enabled(key, db_path=db_path) is True


def test_notes(db_path):
    nid = add_note("Title", "Body", "tag", db_path=db_path)
    assert nid > 0
    assert list_notes(db_path)[0]["title"] == "Title"


def test_init_idempotent(db_path):
    n1 = len(list_projects(db_path))
    init_db(db_path)
    n2 = len(list_projects(db_path))
    assert n1 == n2
