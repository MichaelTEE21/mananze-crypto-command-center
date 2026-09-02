"""User auth — password hashing (stdlib scrypt) and session helpers.

Session helpers are Streamlit-aware when available but work without Streamlit for tests.
Never accept or store seed phrases / private keys.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path
from typing import Any, Optional

from mccc.db import connect, utc_now

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64
_HASH_PREFIX = "scrypt"

SECRET_MARKERS = ("seed", "mnemonic", "private key", "privkey", "recovery phrase")


def _refuse_secrets(text: str) -> None:
    lowered = (text or "").lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise ValueError("Seed phrases and private keys are not allowed")


def hash_password(password: str, *, salt: Optional[bytes] = None) -> str:
    """Hash password with hashlib.scrypt. Returns 'scrypt$salt_hex$hash_hex'."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    _refuse_secrets(password)
    salt_b = salt if salt is not None else secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt_b,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return f"{_HASH_PREFIX}${salt_b.hex()}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = password_hash.split("$")
        if len(parts) != 3 or parts[0] != _HASH_PREFIX:
            return False
        salt_b = bytes.fromhex(parts[1])
        expected = parts[2]
        candidate = hash_password(password, salt=salt_b)
        return hmac.compare_digest(candidate.split("$")[2], expected)
    except Exception:
        return False


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _valid_email(email: str) -> bool:
    # Practical check — not full RFC
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def register_user(
    email: str,
    password: str,
    display_name: str = "",
    experience_level: str = "",
    onboarding_goals: str = "",
    is_admin: int = 0,
    db_path: Optional[Path] = None,
) -> int:
    email_n = _normalize_email(email)
    if not _valid_email(email_n):
        raise ValueError("Invalid email address")
    _refuse_secrets(password)
    _refuse_secrets(display_name)
    _refuse_secrets(onboarding_goals)
    pw_hash = hash_password(password)
    now = utc_now()
    with connect(db_path) as conn:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email_n,)).fetchone()
        if existing:
            raise ValueError("Email already registered")
        cur = conn.execute(
            """INSERT INTO users
               (email, password_hash, display_name, experience_level, onboarding_goals,
                is_admin, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email_n,
                pw_hash,
                (display_name or "").strip(),
                (experience_level or "").strip(),
                onboarding_goals or "",
                1 if is_admin else 0,
                now,
                now,
            ),
        )
        user_id = int(cur.lastrowid)
        conn.execute(
            """INSERT INTO profiles (user_id, theme, notify_prefs, created_at)
               VALUES (?, 'dark', '{}', ?)""",
            (user_id, now),
        )
        return user_id


def authenticate(email: str, password: str, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    email_n = _normalize_email(email)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email_n,)).fetchone()
        if not row:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        user = dict(row)
        user.pop("password_hash", None)
        return user


def get_user_by_id(user_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return None
        user = dict(row)
        user.pop("password_hash", None)
        return user


def get_user_by_email(email: str, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    email_n = _normalize_email(email)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email_n,)).fetchone()
        if not row:
            return None
        user = dict(row)
        user.pop("password_hash", None)
        return user


# --- Session helpers (Streamlit-optional) ---

_SESSION_KEY = "mccc_user"
_SESSION_STORE: dict[str, Any] = {}  # process-local fallback for tests


def _session_dict() -> dict[str, Any]:
    try:
        import streamlit as st  # type: ignore

        return st.session_state  # type: ignore[return-value]
    except Exception:
        return _SESSION_STORE


def set_session_user(user: dict[str, Any]) -> None:
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    _session_dict()[_SESSION_KEY] = safe


def clear_session_user() -> None:
    store = _session_dict()
    if _SESSION_KEY in store:
        del store[_SESSION_KEY]


def get_session_user() -> Optional[dict[str, Any]]:
    return _session_dict().get(_SESSION_KEY)


def require_session_user() -> dict[str, Any]:
    user = get_session_user()
    if not user:
        raise PermissionError("Not authenticated")
    return user


def login(email: str, password: str, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    user = authenticate(email, password, db_path=db_path)
    if user:
        set_session_user(user)
    return user


def logout() -> None:
    clear_session_user()


def auth_secret() -> str:
    """Optional cookie salt from env; generated ephemeral if unset (dev only)."""
    secret = os.environ.get("AUTH_SECRET", "").strip()
    if secret:
        return secret
    # Ephemeral fallback — sessions won't survive process restart
    if "_auth_ephemeral" not in _SESSION_STORE:
        _SESSION_STORE["_auth_ephemeral"] = secrets.token_hex(32)
    return str(_SESSION_STORE["_auth_ephemeral"])
