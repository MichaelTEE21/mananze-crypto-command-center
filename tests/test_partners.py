"""Partner / referral link management tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from mccc.partners import (
    AFFILIATE_DISCLOSURE,
    CATEGORIES,
    REFERRAL_LEAVE_DISCLOSURE,
    SEED_PHRASE_WARNING,
    add_partner_link,
    click_analytics,
    delete_partner_link,
    get_outbound_url,
    list_partner_links,
    normalize_partner_category,
    partner_ecosystem_summary,
    record_click,
    resolve_outbound,
    resolve_visit_url,
    seed_demo_partners,
    set_partner_status,
    update_partner_link,
)


def test_categories_v26():
    assert CATEGORIES == ("Wallets", "CEX", "DEX", "Explorers", "Tools", "Education")


def test_normalize_legacy_categories():
    assert normalize_partner_category("Wallet") == "Wallets"
    assert normalize_partner_category("Crypto Tool") == "Tools"
    assert normalize_partner_category("Partner") == "Tools"
    assert normalize_partner_category("Explorer") == "Explorers"
    assert normalize_partner_category("Wallets") == "Wallets"


def test_resolve_prefers_referral():
    link = {
        "official_url": "https://example.com/official",
        "referral_url": "https://example.com/ref/demo",
    }
    assert resolve_visit_url(link) == "https://example.com/ref/demo"
    d = resolve_outbound(link)
    assert d["url"] == "https://example.com/ref/demo"
    assert d["used_referral"] is True


def test_resolve_falls_back_to_official():
    link = {"official_url": "https://example.com/official", "referral_url": ""}
    assert resolve_visit_url(link) == "https://example.com/official"
    link2 = {"official_url": "https://example.com/official", "referral_url": "   "}
    assert resolve_visit_url(link2) == "https://example.com/official"
    d = resolve_outbound(link2)
    assert d["used_referral"] is False


def test_resolve_outbound_disabled_falls_back_official_when_required():
    link = {
        "id": 1,
        "name": "X",
        "category": "CEX",
        "official_url": "https://example.com/official",
        "referral_url": "https://example.com/ref",
        "status": "Disabled",
    }
    d = resolve_outbound(link, require_active=True)
    assert d["url"] == "https://example.com/official"
    assert d["used_referral"] is False


def test_seed_demo_partners_and_public_list(db_path):
    rows = list_partner_links(db_path=db_path)
    assert len(rows) >= 1
    assert any(
        "DEMO" in r["name"].upper() or "DEMO" in (r.get("description") or "").upper()
        for r in rows
    )
    assert seed_demo_partners(db_path=db_path) == 0
    cats = {r["category"] for r in rows}
    assert cats.issubset(set(CATEGORIES))


def test_disabled_excluded_from_public_list(db_path):
    lid = add_partner_link(
        "Temp Wallet",
        "Wallets",
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


def test_crud_update_and_delete(db_path):
    lid = add_partner_link(
        "CRUD Tool",
        "Tools",
        "https://example.com/tool-a",
        referral_url="",
        db_path=db_path,
    )
    update_partner_link(
        lid,
        referral_url="https://example.com/ref-a",
        description="updated",
        db_path=db_path,
    )
    out = get_outbound_url(lid, db_path=db_path, require_active=True)
    assert out is not None
    assert out["url"] == "https://example.com/ref-a"
    assert out["used_referral"] is True
    delete_partner_link(lid, db_path=db_path)
    assert get_outbound_url(lid, db_path=db_path) is None


def test_record_click_increments_aggregates(db_path):
    lid = add_partner_link(
        "Click Target CEX",
        "CEX",
        "https://example.com/cex2",
        referral_url="https://example.com/ref/demo2",
        db_path=db_path,
    )
    before = click_analytics(db_path=db_path)
    record_click(lid, db_path=db_path, source_page="unit_test")
    record_click(lid, db_path=db_path, source_page="unit_test")
    after = click_analytics(db_path=db_path)
    assert after["total_clicks"] == before["total_clicks"] + 2
    assert after["per_category"]["CEX"] >= before["per_category"].get("CEX", 0) + 2
    plat = next(p for p in after["per_platform"] if p["id"] == lid)
    assert plat["clicks"] == 2
    assert "per_date" in after
    assert isinstance(after["per_date"], list)


def test_legacy_category_filter_wallet(db_path):
    """Filtering by legacy 'Wallet' still returns Wallets rows after migration."""
    lid = add_partner_link(
        "Legacy Filter Wallet",
        "Wallet",  # accepted via normalize
        "https://example.com/w",
        db_path=db_path,
    )
    rows = list_partner_links(status="Active", category="Wallet", db_path=db_path)
    assert any(r["id"] == lid for r in rows)
    assert all(r["category"] == "Wallets" for r in rows if r["id"] == lid)


def test_ecosystem_summary(db_path):
    s = partner_ecosystem_summary(db_path=db_path)
    assert s["active_total"] >= 1
    assert set(s["by_category"].keys()) == set(CATEGORIES)


def test_seed_phrase_warning_constant():
    assert "seed phrase" in SEED_PHRASE_WARNING.lower()
    assert "private key" in SEED_PHRASE_WARNING.lower()


def test_disclosure_copy_present():
    assert "partner" in AFFILIATE_DISCLOSURE.lower() or "referral" in AFFILIATE_DISCLOSURE.lower()
    assert "leaving" in REFERRAL_LEAVE_DISCLOSURE.lower()
    assert "safer" in REFERRAL_LEAVE_DISCLOSURE.lower()
    assert "seed" in REFERRAL_LEAVE_DISCLOSURE.lower()


def test_partner_directory_page_smoke_no_key_fields():
    root = Path(__file__).resolve().parents[1]
    pages = [
        root / "pages" / "11_Partner_Directory.py",
        root / "pages" / "12_Admin_Partner_Links.py",
        root / "pages" / "19_Wallet_Directory.py",
        root / "pages" / "33_Crypto_Directory.py",
        root / "pages" / "34_DEX_Hub.py",
        root / "pages" / "35_Admin_Partner_Analytics.py",
    ]
    for page in pages:
        src = page.read_text(encoding="utf-8")
        lowered = src.lower()
        assert "seed" in lowered or "SEED_PHRASE" in src
        # Must not solicit secrets as form inputs (educational lesson stems like private_key.md OK)
        assert 'text_input("seed' not in lowered
        assert 'text_input("private' not in lowered
        assert 'text_input("mnemonic' not in lowered
        assert "mnemonic" not in lowered or "never" in lowered
        assert "ref=" not in lowered or "example.com" in lowered
