"""Phase 1 foundation — universal search, wallet public-only, calendar schema, routing helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from mccc.calendar_service import (
    CALENDAR_EVENT_TYPES,
    ensure_ready,
    intelligence_hook,
    list_events,
    month_grid,
    parse_year_month,
)
from mccc.db import add_calendar_event, init_db, list_calendar_events
from mccc.token_intel import DATA_UNAVAILABLE, build_token_market_snapshot, format_money
from mccc.universal_search import (
    analyse_session_payload,
    chip_for_entity,
    detect_search_entity,
    homepage_search_placeholder,
    unified_search_results,
)
from mccc.wallets import validate_public_address


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    db = tmp_path / "p1.db"
    init_db(db)
    return db


def test_homepage_placeholder_mentions_entities():
    p = homepage_search_placeholder()
    assert "wallet" in p.lower()
    assert "token" in p.lower()


def test_detect_wallet_0x():
    addr = "0x" + "ab" * 20
    d = detect_search_entity(addr)
    assert d.ok
    assert d.entity_type == "wallet"
    assert d.chip == "Wallet"


def test_detect_dollar_ticker_token():
    d = detect_search_entity("$BTC")
    assert d.ok
    assert d.entity_type == "token"
    assert d.chip == "Token"


def test_detect_protocol_uniswap():
    d = detect_search_entity("uniswap")
    assert d.ok
    assert d.entity_type == "protocol"
    assert d.chip == "Protocol"


def test_detect_rejects_mnemonic():
    phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    d = detect_search_entity(phrase)
    assert not d.ok
    assert d.rejected_secret


def test_detect_rejects_privkey():
    d = detect_search_entity("0x" + "cd" * 32)
    assert not d.ok
    assert d.rejected_secret


def test_analyse_session_payload_keys():
    d = detect_search_entity("bitcoin")
    payload = analyse_session_payload(d)
    assert "intel_report_q" in payload
    assert payload["intel_report_q"]
    assert "mccc_analyse_entity_hint" in payload


def test_chip_for_entity():
    assert chip_for_entity("wallet") == "Wallet"
    assert chip_for_entity("token") == "Token"


def test_unified_search_runs(tmp_db: Path):
    out = unified_search_results("bitcoin", db_path=tmp_db, limit_per=5)
    assert "detected" in out
    assert out["detected"]["entity_type"] == "token"
    assert "typed_hits" in out


def test_wallet_public_only_validation():
    addr = validate_public_address("0x" + "11" * 20, "ethereum")
    assert addr.startswith("0x")
    with pytest.raises(ValueError):
        validate_public_address(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "ethereum",
        )
    with pytest.raises(ValueError):
        validate_public_address("0x" + "aa" * 32, "ethereum")


def test_calendar_schema_and_types(tmp_db: Path):
    ensure_ready(tmp_db)
    assert "airdrop" in CALENDAR_EVENT_TYPES
    assert "unlock" in CALENDAR_EVENT_TYPES
    assert "burn" in CALENDAR_EVENT_TYPES
    events = list_events(db_path=tmp_db)
    assert isinstance(events, list)
    # seed should insert DEMO rows on empty
    assert any(e.get("is_demo") for e in events)


def test_calendar_add_and_filter(tmp_db: Path):
    ensure_ready(tmp_db)
    eid = add_calendar_event(
        "Test unlock placeholder",
        "unlock",
        "2026-09-20",
        source="unit test",
        data_quality="UNVERIFIED",
        is_demo=True,
        entity_type="token",
        entity_ref="bitcoin",
        db_path=tmp_db,
    )
    assert eid > 0
    rows = list_calendar_events(event_type="unlock", db_path=tmp_db)
    assert any(r["id"] == eid for r in rows)
    hook = intelligence_hook(rows[0] if rows[0]["id"] == eid else next(r for r in rows if r["id"] == eid))
    assert hook is not None
    assert hook["intel_report_q"] == "bitcoin"


def test_month_grid_and_parse():
    y, m = parse_year_month("2026-09")
    assert (y, m) == (2026, 9)
    grid = month_grid(2026, 9)
    assert len(grid) >= 4
    assert all(len(w) == 7 for w in grid)


def test_token_snapshot_placeholders():
    snap = build_token_market_snapshot("bitcoin")
    assert snap.holders_status == DATA_UNAVAILABLE
    assert snap.tokenomics_status == DATA_UNAVAILABLE
    assert snap.locks_status == DATA_UNAVAILABLE
    assert snap.provenance is not None
    assert format_money(None) == DATA_UNAVAILABLE
    assert "$" in format_money(1234.5)


def test_version_bump():
    from mccc import __version__

    assert __version__ == "2.6.0"
