"""Auth module tests — scrypt hashing, register/login, session helpers."""
from __future__ import annotations

import pytest

from mccc.auth import (
    authenticate,
    clear_session_user,
    get_session_user,
    get_user_by_id,
    hash_password,
    login,
    logout,
    register_user,
    set_session_user,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    h = hash_password("correct-horse-battery")
    assert h.startswith("scrypt$")
    assert verify_password("correct-horse-battery", h) is True
    assert verify_password("wrong-password-xx", h) is False


def test_hash_rejects_short_password():
    with pytest.raises(ValueError):
        hash_password("short")


def test_hash_rejects_seed_marker():
    with pytest.raises(ValueError):
        hash_password("my seed phrase is not allowed here")


def test_register_and_authenticate(db_path):
    uid = register_user(
        "alice@example.com",
        "securepass1",
        display_name="Alice",
        experience_level="beginner",
        db_path=db_path,
    )
    assert uid > 0
    user = authenticate("alice@example.com", "securepass1", db_path=db_path)
    assert user is not None
    assert user["email"] == "alice@example.com"
    assert "password_hash" not in user
    assert authenticate("alice@example.com", "nope-nope1", db_path=db_path) is None


def test_register_duplicate_email(db_path):
    register_user("bob@example.com", "securepass1", db_path=db_path)
    with pytest.raises(ValueError):
        register_user("bob@example.com", "anotherpass1", db_path=db_path)


def test_register_invalid_email(db_path):
    with pytest.raises(ValueError):
        register_user("not-an-email", "securepass1", db_path=db_path)


def test_get_user_by_id(db_path):
    uid = register_user("carol@example.com", "securepass1", db_path=db_path)
    user = get_user_by_id(uid, db_path=db_path)
    assert user and user["id"] == uid
    assert "password_hash" not in user


def test_session_helpers(db_path):
    clear_session_user()
    assert get_session_user() is None
    uid = register_user("dave@example.com", "securepass1", db_path=db_path)
    user = login("dave@example.com", "securepass1", db_path=db_path)
    assert user is not None
    assert get_session_user()["id"] == uid
    logout()
    assert get_session_user() is None
    set_session_user({"id": uid, "email": "dave@example.com"})
    assert get_session_user()["email"] == "dave@example.com"
    clear_session_user()
