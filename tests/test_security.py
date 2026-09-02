"""Security rejection tests — credential-like inputs must never be accepted."""
from __future__ import annotations

import pytest

from mccc.auth import hash_password, register_user
from mccc.db import add_wallet, init_db, list_settings, set_setting, get_setting
from mccc.security import (
    SensitiveCredentialError,
    contains_credential_markers,
    is_sensitive_credential,
    looks_like_hex_private_key,
    looks_like_mnemonic,
    reject_sensitive_credential,
)
from mccc.wallets import validate_public_address


TWELVE = " ".join(
    [
        "abandon", "ability", "able", "about", "above", "absent",
        "absorb", "abstract", "absurd", "abuse", "access", "accident",
    ]
)
TWENTY_FOUR = TWELVE + " " + " ".join(
    [
        "account", "accuse", "achieve", "acid", "acoustic", "acquire",
        "across", "act", "action", "actor", "actress", "actual",
    ]
)
HEX64 = "a" * 64
HEX64_0X = "0x" + "b" * 64


def test_looks_like_mnemonic_12_and_24():
    assert looks_like_mnemonic(TWELVE) is True
    assert looks_like_mnemonic(TWENTY_FOUR) is True
    assert looks_like_mnemonic("abandon ability able") is False
    assert looks_like_mnemonic("0x" + "a" * 40) is False


def test_looks_like_hex_private_key():
    assert looks_like_hex_private_key(HEX64) is True
    assert looks_like_hex_private_key(HEX64_0X) is True
    # Public address must NOT be treated as privkey
    assert looks_like_hex_private_key("0x" + "a" * 40) is False
    assert looks_like_hex_private_key("hello") is False


def test_marker_phrases():
    assert contains_credential_markers("here is my private key")
    assert contains_credential_markers("SEED PHRASE below")
    assert contains_credential_markers("2fa secret: abc")
    assert contains_credential_markers("wallet password xyz")
    assert not contains_credential_markers("public research notes on bridges")


def test_reject_sensitive_credential_raises():
    with pytest.raises(SensitiveCredentialError):
        reject_sensitive_credential(TWELVE, field="notes")
    with pytest.raises(SensitiveCredentialError):
        reject_sensitive_credential(HEX64, field="addr")
    with pytest.raises(SensitiveCredentialError):
        reject_sensitive_credential("mnemonic dump", field="x")
    assert reject_sensitive_credential("safe public text", field="x") == "safe public text"


def test_is_sensitive_credential_helpers():
    assert is_sensitive_credential(TWELVE)
    assert is_sensitive_credential("recovery phrase please")
    assert not is_sensitive_credential("")
    assert not is_sensitive_credential("  ")
    assert not is_sensitive_credential("Layer-2 research brief")


def test_validate_public_address_rejects_secrets():
    with pytest.raises(ValueError):
        validate_public_address(TWELVE)
    with pytest.raises(ValueError):
        validate_public_address(HEX64)
    with pytest.raises(ValueError):
        validate_public_address("my private key 0xdead")
    # Valid public address still OK
    addr = validate_public_address("0x" + "c" * 40)
    assert addr.startswith("0x")


def test_add_wallet_rejects_mnemonic_and_privkey(db_path):
    with pytest.raises(ValueError):
        add_wallet("Bad", TWELVE, db_path=db_path)
    with pytest.raises(ValueError):
        add_wallet("Bad", HEX64_0X, db_path=db_path)
    with pytest.raises(ValueError):
        add_wallet("label with seed phrase words", "0x" + "d" * 40, db_path=db_path)
    with pytest.raises(ValueError):
        add_wallet("Ok", "0x" + "e" * 40, notes="contains mnemonic backup", db_path=db_path)


def test_add_wallet_accepts_public(db_path):
    wid = add_wallet("Watch", "0x" + "f" * 40, "ethereum", "public only", db_path=db_path)
    assert wid > 0


def test_auth_rejects_credential_like_password():
    with pytest.raises(ValueError):
        hash_password("my seed phrase is not allowed here")
    with pytest.raises(ValueError):
        hash_password("contains private key material!!")
    with pytest.raises(ValueError):
        hash_password(TWELVE)


def test_register_rejects_secret_in_display_name(db_path):
    with pytest.raises(ValueError):
        register_user(
            "ok@example.com",
            "securepass1",
            display_name="user mnemonic holder",
            db_path=db_path,
        )


def test_schema_v2_tables_exist(db_path):
    from mccc.db import connect

    needed = {
        "exchanges",
        "resources",
        "announcements",
        "bookmarks",
        "research_events",
        "project_tags",
        "app_settings",
    }
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in rows}
    assert needed.issubset(names)
    # research_notes.project_id
    with connect(db_path) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(research_notes)").fetchall()}
    assert "project_id" in cols


def test_app_settings_roundtrip(db_path):
    set_setting("theme", "dark", db_path=db_path)
    assert get_setting("theme", db_path=db_path) == "dark"
    assert get_setting("missing", default="x", db_path=db_path) == "x"
    assert "theme" in list_settings(db_path=db_path)


def test_init_idempotent_keeps_v2(db_path):
    set_setting("keep", "1", db_path=db_path)
    init_db(db_path)
    assert get_setting("keep", db_path=db_path) == "1"


def test_services_facade_imports():
    from mccc.services import market, ai
    from mccc.market_provider import get_default_provider as legacy
    from mccc.services.market import get_default_provider as via_service

    assert legacy is via_service or callable(via_service)
    assert callable(market.get_default_provider)
    assert callable(ai.answer)
    assert callable(ai.contains_secrets)
