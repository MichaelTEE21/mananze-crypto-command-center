"""Partner / referral link management tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from mccc.partners import (
    SEED_PHRASE_WARNING,
    add_partner_link,
    click_analytics,
    list_partner_links,
    record_click,
    resolve_visit_url,
    seed_demo_partners,
    set_partner_status,
)


def test_resolve_prefers_referral():
    link = {
        "official_url": "https://example.com/official",
        "referral_url": "https://example.com/ref/demo",
    }
    assert resolve_visit_url(link) == "https://example.com/ref/demo"


def test_resolve_falls_back_to_official():
    link = {"official_url": "https://example.com/official", "referral_url": ""}
    assert resolve_visit_url(link) == "https://example.com/official"
    link2 = {"official_url": "https://example.com/official", "referral_url": "   "}
    assert resolve_visit_url(link2) == "https://example.com/official"


def test_seed_demo_partners_and_public_list(db_path):
    # init_db already seeds; count should be > 0 and DEMO labelled
    rows = list_partner_links(db_path=db_path)
    assert len(rows) >= 1
    assert any("DEMO" in r["name"].upper() or "DEMO" in (r.get("description") or "").upper() for r in rows)
    # Idempotent seed
    assert seed_demo_partners(db_path=db_path) == 0


def test_disabled_excluded_from_public_list(db_path):
    lid = add_partner_link(
        "Temp Wallet",
        "Wallet",
        "https://example.com/tmp",
        status="Active",
        db_path=db_path,
    )
    active = list_partner_links(status="Active", db_path=db_path)
    assert any(r["id"] == lid for r in active)
    set_partner_status(lid, "Disabled", db_path=db_path)
    active2 = list_partner_links(status="Active", db_path=db_path)
    assert all(r["id"] != lid for r in active2)
    all_rows = list_partner_links(db_path=db_path)
    assert any(r["id"] == lid and r["status"] == "Disabled" for r in all_rows)


def test_record_click_increments_aggregates(db_path):
    lid = add_partner_link(
        "Click Target CEX",
        "CEX",
        "https://example.com/cex2",
        referral_url="https://example.com/ref/demo2",
        db_path=db_path,
    )
    before = click_analytics(db_path=db_path)
    record_click(lid, db_path=db_path)
    record_click(lid, db_path=db_path)
    after = click_analytics(db_path=db_path)
    assert after["total_clicks"] == before["total_clicks"] + 2
    assert after["per_category"]["CEX"] >= before["per_category"].get("CEX", 0) + 2
    plat = next(p for p in after["per_platform"] if p["id"] == lid)
    assert plat["clicks"] == 2


def test_seed_phrase_warning_constant():
    assert "seed phrase" in SEED_PHRASE_WARNING.lower()
    assert "private key" in SEED_PHRASE_WARNING.lower()


def test_partner_directory_page_smoke_no_key_fields():
    """Optional smoke: page source must not solicit seed/private key input."""
    root = Path(__file__).resolve().parents[1]
    page = (root / "pages" / "11_Partner_Directory.py").read_text(encoding="utf-8")
    admin = (root / "pages" / "12_Admin_Partner_Links.py").read_text(encoding="utf-8")
    for src in (page, admin):
        lowered = src.lower()
        assert "seed phrase" in lowered or "seed_phrase" in lowered or "SEED_PHRASE" in src
        # Must not have input fields requesting secrets
        assert "private_key" not in lowered
        assert 'type="password"' not in lowered or "admin password" in lowered
        assert "mnemonic" not in lowered or "never" in lowered
