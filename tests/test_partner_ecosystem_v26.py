"""MCCC 2.6.0 Partner Ecosystem — directories, hubs, routing, security, analytics."""
from __future__ import annotations

from pathlib import Path

from mccc import __version__
from mccc.partners import (
    CATEGORIES,
    REFERRAL_LEAVE_DISCLOSURE,
    add_partner_link,
    click_analytics,
    get_outbound_url,
    list_partner_links,
    record_click,
    resolve_outbound,
)
from mccc.security import is_sensitive_credential, reject_sensitive_credential, SensitiveCredentialError
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_version_260():
    assert __version__ == "2.6.0"


def test_crypto_directory_page_exists_and_uses_central_service():
    src = (ROOT / "pages" / "33_Crypto_Directory.py").read_text(encoding="utf-8")
    assert "list_partner_links" in src
    assert "partner_cta" in src
    assert "referral_leave_disclosure" in src or "REFERRAL" in src
    for cat in CATEGORIES:
        assert cat in src or cat.upper() in src or "CATEGORIES" in src
    assert "https://binance.com" not in src.lower()
    assert "hardcode" not in src.lower() or "never" in src.lower()


def test_hub_pages_never_ask_keys_banner():
    for rel in (
        "pages/19_Wallet_Directory.py",
        "pages/20_Exchange_Directory.py",
        "pages/34_DEX_Hub.py",
    ):
        src = (ROOT / rel).read_text(encoding="utf-8")
        low = src.lower()
        assert "seed" in low
        assert "private key" in low or "private keys" in low
        assert 'type="password"' not in low or "admin password" in low


def test_command_center_partner_ecosystem_section():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "partner_ecosystem_summary" in src
    assert "Partner ecosystem" in src or "partner ecosystem" in src.lower()
    assert "33_Crypto_Directory" in src
    assert "34_DEX_Hub" in src


def test_admin_analytics_page_no_pii_fields():
    src = (ROOT / "pages" / "35_Admin_Partner_Analytics.py").read_text(encoding="utf-8")
    low = src.lower()
    assert "click_analytics" in src
    assert "ip" not in low.split("pii")[0] or "no ip" in low or "no ip," in low or "aggregates" in low
    assert "user_agent" not in low
    assert "fingerprint" not in low


def test_routing_fallback_and_active_gate(db_path):
    lid = add_partner_link(
        "Route Me",
        "DEX",
        "https://example.com/dex-official",
        referral_url="https://example.com/dex-ref",
        status="Active",
        db_path=db_path,
    )
    d = get_outbound_url(lid, db_path=db_path, require_active=True)
    assert d["url"] == "https://example.com/dex-ref"
    # disable → official only
    from mccc.partners import set_partner_status

    set_partner_status(lid, "Disabled", db_path=db_path)
    d2 = get_outbound_url(lid, db_path=db_path, require_active=True)
    assert d2["url"] == "https://example.com/dex-official"
    assert d2["used_referral"] is False


def test_click_analytics_has_date_dimension(db_path):
    rows = list_partner_links(status="Active", db_path=db_path)
    assert rows
    record_click(rows[0]["id"], db_path=db_path, source_page="v26_test")
    a = click_analytics(db_path=db_path)
    assert a["total_clicks"] >= 1
    assert a["per_date"]
    assert "day" in a["per_date"][0]
    assert "clicks" in a["per_date"][0]


def test_disclosure_on_decision_surfaces():
    assert "external" in REFERRAL_LEAVE_DISCLOSURE.lower()
    for rel in (
        "pages/33_Crypto_Directory.py",
        "pages/11_Partner_Directory.py",
        "pages/34_DEX_Hub.py",
        "src/mccc/ui.py",
    ):
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert (
            "referral_leave_disclosure" in src
            or "REFERRAL_LEAVE_DISCLOSURE" in src
            or "leaving MCCC" in src
        )


def test_partner_pages_reject_credential_patterns_in_source():
    """Static: hub/directory sources must not solicit wallet passwords / seeds as inputs."""
    for rel in (
        "pages/33_Crypto_Directory.py",
        "pages/19_Wallet_Directory.py",
        "pages/34_DEX_Hub.py",
    ):
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert "st.text_input(\"Seed" not in src
        assert "st.text_input(\"Private" not in src
        assert "recovery phrase" not in src.lower() or "never" in src.lower()


def test_security_module_still_blocks_seeds():
    twelve = " ".join(
        [
            "abandon", "ability", "able", "about", "above", "absent",
            "absorb", "abstract", "absurd", "abuse", "access", "accident",
        ]
    )
    assert is_sensitive_credential(twelve)
    with pytest.raises(SensitiveCredentialError):
        reject_sensitive_credential(twelve, field="notes")


def test_no_hardcoded_partner_urls_across_hub_pages():
    """Pages must not embed live affiliate URLs — only example.com DEMO or DB-driven."""
    forbidden_snippets = [
        "ref/binance",
        "affiliate=",
        "partner_id=",
        "utm_campaign=mccc_hardcoded",
    ]
    for rel in (
        "pages/11_Partner_Directory.py",
        "pages/19_Wallet_Directory.py",
        "pages/20_Exchange_Directory.py",
        "pages/33_Crypto_Directory.py",
        "pages/34_DEX_Hub.py",
        "pages/17_Start_Here.py",
        "app.py",
    ):
        src = (ROOT / rel).read_text(encoding="utf-8").lower()
        for snip in forbidden_snippets:
            assert snip not in src, f"{rel} contains {snip}"
