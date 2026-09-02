"""Phase 12–14: auth polish, PRO gating, config, security regressions."""
from __future__ import annotations

import os

import pytest

from mccc.auth import (
    authenticate,
    change_password,
    clear_session_user,
    delete_account,
    get_session_user,
    get_user_by_id,
    login,
    maybe_bootstrap_admin,
    register_user,
    set_admin,
    update_profile,
    verify_password,
)
from mccc.config import config_status_public, validate_config
from mccc.db import add_airdrop, add_project, add_wallet, connect, get_setting, set_setting
from mccc.subscriptions import (
    PRO_PAYMENTS_MESSAGE,
    check_limit,
    free_limits,
    has_pro_feature,
    is_pro,
    require_can_add,
    set_tier,
)
from mccc import __version__


def test_version_is_release():
    assert __version__ == "2.0.0"


def test_change_password_scrypt(db_path):
    uid = register_user("pwchange@example.com", "oldpassword1", db_path=db_path)
    change_password(uid, "oldpassword1", "newpassword1", db_path=db_path)
    assert authenticate("pwchange@example.com", "oldpassword1", db_path=db_path) is None
    assert authenticate("pwchange@example.com", "newpassword1", db_path=db_path) is not None


def test_change_password_rejects_wrong_current(db_path):
    uid = register_user("pwbad@example.com", "oldpassword1", db_path=db_path)
    with pytest.raises(ValueError):
        change_password(uid, "nope-nope1", "newpassword1", db_path=db_path)


def test_update_profile_and_onboarding(db_path):
    uid = register_user("prof@example.com", "securepass1", db_path=db_path)
    u = update_profile(
        uid,
        display_name="Researcher",
        experience_level="beginner",
        onboarding_goals="goals=Learn basics; risk=low; chains=ethereum",
        db_path=db_path,
    )
    assert u["display_name"] == "Researcher"
    assert u["experience_level"] == "beginner"
    assert "Learn basics" in u["onboarding_goals"]


def test_update_profile_rejects_seed(db_path):
    uid = register_user("seedprof@example.com", "securepass1", db_path=db_path)
    with pytest.raises(ValueError):
        update_profile(uid, display_name="my seed phrase wallet", db_path=db_path)


def test_soft_delete_account(db_path):
    uid = register_user("gone@example.com", "securepass1", db_path=db_path)
    login("gone@example.com", "securepass1", db_path=db_path)
    assert get_session_user() is not None
    delete_account(uid, password="securepass1", hard=False, db_path=db_path)
    assert get_session_user() is None
    assert authenticate("gone@example.com", "securepass1", db_path=db_path) is None
    assert get_user_by_id(uid, db_path=db_path) is None
    # soft row still exists with deleted_at
    with connect(db_path) as conn:
        row = conn.execute("SELECT deleted_at FROM users WHERE id=?", (uid,)).fetchone()
        assert row and row["deleted_at"]


def test_bootstrap_admin_from_env(db_path, monkeypatch):
    uid = register_user("adminboot@example.com", "securepass1", db_path=db_path)
    monkeypatch.setenv("MCCC_BOOTSTRAP_ADMIN_EMAIL", "adminboot@example.com")
    # reset module flag
    import mccc.auth as auth_mod

    auth_mod._BOOTSTRAP_DONE = False
    out = maybe_bootstrap_admin(db_path=db_path)
    assert out == uid
    user = get_user_by_id(uid, db_path=db_path)
    assert user and user["is_admin"] == 1


def test_bootstrap_admin_from_settings(db_path, monkeypatch):
    monkeypatch.delenv("MCCC_BOOTSTRAP_ADMIN_EMAIL", raising=False)
    uid = register_user("settingsadmin@example.com", "securepass1", db_path=db_path)
    set_setting("bootstrap_admin_email", "settingsadmin@example.com", db_path=db_path)
    assert get_setting("bootstrap_admin_email", db_path=db_path) == "settingsadmin@example.com"
    import mccc.auth as auth_mod

    auth_mod._BOOTSTRAP_DONE = False
    maybe_bootstrap_admin(db_path=db_path)
    assert get_user_by_id(uid, db_path=db_path)["is_admin"] == 1


def test_free_limits_soft_gate(db_path, monkeypatch):
    monkeypatch.delenv("MCCC_PRO_UNLOCK", raising=False)
    set_tier("free", db_path=db_path)
    limits = free_limits()
    assert limits["projects"] >= 1
    # seed already created demo projects — count them
    gate = check_limit("projects", db_path=db_path)
    assert "count" in gate
    # Force limit hit via current_count
    blocked = check_limit("projects", db_path=db_path, current_count=limits["projects"])
    assert blocked["allowed"] is False
    assert blocked["upgrade_cta"] is True
    assert PRO_PAYMENTS_MESSAGE.split()[0] in blocked["message"] or "PRO" in blocked["message"]
    with pytest.raises(ValueError):
        # temporarily monkeypatch count by using require with saturated DB:
        # add until over — use current_count path via checking require after filling
        from mccc import subscriptions as sub

        original = sub.count_resource
        sub.count_resource = lambda resource, db_path=None: limits["wallets"]  # type: ignore
        try:
            require_can_add("wallets", db_path=db_path)
        finally:
            sub.count_resource = original


def test_pro_unlock_unlimited(db_path, monkeypatch):
    monkeypatch.setenv("MCCC_PRO_UNLOCK", "1")
    gate = check_limit("projects", db_path=db_path)
    assert gate["allowed"] is True
    assert gate.get("unlimited") is True
    monkeypatch.delenv("MCCC_PRO_UNLOCK", raising=False)


def test_has_pro_feature_flag_or_tier(db_path, monkeypatch):
    monkeypatch.delenv("MCCC_PRO_UNLOCK", raising=False)
    set_tier("free", db_path=db_path)
    from mccc.db import set_feature_flag

    set_feature_flag("pro_advanced_analytics", False, db_path=db_path)
    assert has_pro_feature("pro_advanced_analytics", db_path=db_path) is False
    set_feature_flag("pro_advanced_analytics", True, db_path=db_path)
    assert has_pro_feature("pro_advanced_analytics", db_path=db_path) is True
    set_feature_flag("pro_advanced_analytics", False, db_path=db_path)
    set_tier("pro", db_path=db_path)
    assert has_pro_feature("pro_advanced_analytics", db_path=db_path) is True
    set_tier("free", db_path=db_path)


def test_validate_config_never_crashes():
    warns = validate_config()
    assert isinstance(warns, list)
    status = config_status_public()
    assert status["ok"] is True
    assert "optional_keys" in status
    # never includes raw secret values
    for v in status["optional_keys"].values():
        assert "set" in v
        assert "purpose" in v


def test_payments_message_honest():
    assert "not yet enabled" in PRO_PAYMENTS_MESSAGE.lower()


def test_security_regression_password_change_rejects_mnemonic(db_path):
    uid = register_user("sec@example.com", "securepass1", db_path=db_path)
    twelve = " ".join(
        [
            "abandon", "ability", "able", "about", "above", "absent",
            "absorb", "abstract", "absurd", "abuse", "access", "accident",
        ]
    )
    with pytest.raises(ValueError):
        change_password(uid, "securepass1", twelve, db_path=db_path)


def test_deleted_at_column_exists(db_path):
    with connect(db_path) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    assert "deleted_at" in cols
