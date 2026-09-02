"""Tests for Phases 7–11: education categories, resources, search, announcements, AI provider."""
from __future__ import annotations

from pathlib import Path

import pytest

from mccc.announcements import create, expire, list_all, list_published, publish, update
from mccc.ai_service import (
    AssistantProvider,
    OpenAICompatibleProvider,
    RuleBasedProvider,
    answer,
    get_assistant_provider,
    looks_like_market_question,
)
from mccc.bookmarks import delete_bookmark, list_bookmarks, set_favourite
from mccc.db import add_note, add_project, utc_now
from mccc.education import (
    CATEGORIES,
    category_of,
    infer_category_from_name,
    list_lessons,
    lessons_by_category,
    parse_frontmatter,
    score_quiz,
)
from mccc.resources import (
    add_resource,
    delete_resource,
    list_resources,
    record_resource_click,
    search_resources,
    update_resource,
)
from mccc.search import match_query, search_all, search_education, search_projects


def test_education_categories_and_frontmatter(tmp_path):
    md = tmp_path / "bridges.md"
    md.write_text(
        "---\ncategory: INTERMEDIATE\nrelated: l1_l2, defi_basics\n---\n# Bridges\n\nBody\n",
        encoding="utf-8",
    )
    meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
    assert meta["category"] == "INTERMEDIATE"
    assert "l1_l2" in meta["related"]
    assert body.startswith("# Bridges")
    assert infer_category_from_name("advanced_foo") == "ADVANCED"
    assert infer_category_from_name("intermediate_bar") == "INTERMEDIATE"
    assert category_of("defi_basics") in CATEGORIES


def test_education_catalog_has_intermediate_advanced():
    lessons = list_lessons()
    assert lessons
    by = lessons_by_category()
    keys = {L["key"] for L in lessons}
    for needed in ("bridges", "staking", "l1_l2", "mev", "depin", "zk_basics", "ai_agents_crypto", "defi_basics"):
        assert needed in keys
    assert by["INTERMEDIATE"]
    assert by["ADVANCED"]
    assert by["BEGINNER"]


def test_quiz_score_honest():
    assert score_quiz("missing_lesson", [0]) is None
    sc = score_quiz("key_safety", [1])
    assert sc == 1.0
    sc2 = score_quiz("key_safety", [0])
    assert sc2 == 0.0


def test_resources_crud(db_path):
    pid = add_project("ResProj", "ethereum", db_path=db_path)
    rid = add_resource(
        "Official Docs",
        url="https://example.com/docs",
        resource_type="docs",
        project_id=pid,
        is_official=True,
        db_path=db_path,
    )
    assert rid > 0
    rows = list_resources(project_id=pid, db_path=db_path)
    assert any(r["id"] == rid for r in rows)
    update_resource(rid, description="updated", db_path=db_path)
    hit = next(r for r in list_resources(db_path=db_path) if r["id"] == rid)
    assert hit["description"] == "updated"
    assert hit["is_official"] == 1
    record_resource_click(rid, db_path=db_path)
    hit2 = next(r for r in list_resources(db_path=db_path) if r["id"] == rid)
    assert hit2["click_count"] == 1
    assert search_resources("docs", db_path=db_path)
    delete_resource(rid, db_path=db_path)
    assert all(r["id"] != rid for r in list_resources(db_path=db_path))


def test_search_helpers(db_path):
    assert match_query("hello world", "WORLD")
    assert not match_query("hello", "")
    add_project("Bridge Alpha", "ethereum", notes="cross-chain bridge", db_path=db_path)
    hits = search_projects("bridge", db_path=db_path)
    assert any("Bridge" in p["name"] for p in hits)
    edu = search_education("seed")
    assert edu
    bundled = search_all("DEMO", categories=["projects", "education"], db_path=db_path)
    assert "projects" in bundled and "education" in bundled


def test_announcements_publish_expire(db_path):
    aid = create("Hello", "Body", published=False, db_path=db_path)
    assert list_published(db_path=db_path) == [] or all(a["id"] != aid for a in list_published(db_path=db_path))
    publish(aid, True, db_path=db_path)
    assert any(a["id"] == aid for a in list_published(db_path=db_path))
    update(aid, body="Edited", db_path=db_path)
    expire(aid, db_path=db_path)
    assert all(a["id"] != aid for a in list_published(db_path=db_path))
    assert any(a["id"] == aid for a in list_all(db_path=db_path))


def test_bookmarks_list_delete(db_path):
    set_favourite("lesson", "bridges", favourite=True, tags="edu", db_path=db_path)
    rows = list_bookmarks(item_type="lesson", db_path=db_path)
    assert rows
    delete_bookmark(item_type="lesson", item_ref="bridges", db_path=db_path)
    assert not list_bookmarks(item_type="lesson", favourites_only=True, db_path=db_path)


def test_assistant_provider_abstraction(db_path):
    rule = RuleBasedProvider()
    assert isinstance(rule, AssistantProvider) or hasattr(rule, "answer")
    result = rule.answer("airdrop hygiene checklist")
    assert result["mode"] == "rule_based"
    assert "FACT" in result["answer"]
    assert looks_like_market_question("What is the ETH price?")
    market_ans = answer("ETH price please", use_llm=False, db_path=db_path)
    assert market_ans["mode"] == "rule_based"
    assert "DATA" in market_ans["answer"] or "DEMO" in market_ans["answer"] or "LIVE" in market_ans["answer"] or "unavailable" in market_ans["answer"].lower()
    llm = OpenAICompatibleProvider(api_key="")
    assert llm.available is False
    provider = get_assistant_provider(prefer_llm=False)
    assert provider.name == "rule"


def test_notes_project_filter_data(db_path):
    pid = add_project("NoteLink", "solana", db_path=db_path)
    add_note("Linked", "body", "tag", project_id=pid, db_path=db_path)
    add_note("Orphan", "body2", "", project_id=None, db_path=db_path)
    from mccc.db import list_notes

    notes = list_notes(db_path=db_path)
    assert any(n.get("project_id") == pid for n in notes)
    assert any(n.get("project_id") is None and n["title"] == "Orphan" for n in notes)
