"""Helper module tests — wallets, market fallback, assistant."""
from __future__ import annotations

import pytest

from mccc.assistant import match_tips, structure_research_note
from mccc.demo_data import DEMO_BANNER, portfolio_summary
from mccc.market import fetch_prices
from mccc.wallets import balance_rows_for_address, validate_public_address


def test_portfolio_summary_demo():
    s = portfolio_summary()
    assert s["total_usd"] > 0
    assert "DEMO" in s["source"]
    assert "DEMO" in DEMO_BANNER


def test_validate_eth_address():
    addr = validate_public_address("0x" + "a" * 40)
    assert addr.startswith("0x")


def test_validate_demo_address():
    assert validate_public_address("0xDEMO000000000000000000000000000000000001").startswith("0xDEMO")


def test_reject_private_markers():
    with pytest.raises(ValueError):
        validate_public_address("private key abc")
    with pytest.raises(ValueError):
        validate_public_address("seed phrase test")


def test_demo_balances():
    rows = balance_rows_for_address("0xDEMO000000000000000000000000000000000001")
    assert rows
    assert any(r.get("source") == "DEMO" for r in rows)


def test_fetch_prices_shape():
    rows, source, is_live = fetch_prices(timeout=3.0)
    assert isinstance(rows, list) and len(rows) >= 1
    assert "source" in source.lower() or "demo" in source.lower() or "coingecko" in source.lower()
    assert isinstance(is_live, bool)
    assert "current_price" in rows[0]


def test_assistant_match():
    tips = match_tips("airdrop sybil eligibility")
    assert tips
    assert any("airdrop" in t["title"].lower() or "airdrop" in t["id"] for t in tips)


def test_structure_note():
    note = structure_research_note("Bridge risk", "L2 example")
    assert "Bridge risk" in note["title"]
    assert "Not financial advice" in note["body"]
    assert "Sources" in note["body"]
