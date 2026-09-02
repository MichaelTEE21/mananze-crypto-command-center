"""User auth — password hashing (stdlib scrypt) and session helpers.

Session helpers (Streamlit-aware, process-local fallback for tests)
-------------------------------------------------------------------
- ``set_session_user(user)`` — store safe user dict (no password_hash) under
  session key ``mccc_user``.
- ``get_session_user()`` — current user or None (guest / single-user mode).
- ``clear_session_user()`` / ``logout()`` — clear session.
- ``require_session_user()`` — raise PermissionError if guest.
- ``login(email, password)`` — authenticate + set session.
- Soft limits for free tier still apply when not logged in (guest = free).

Admin bootstrap
---------------
Set ``MCCC_BOOTSTRAP_ADMIN_EMAIL`` to an existing user's email (or register that
email first). On ``maybe_bootstrap_admin()`` (called from page_setup / Account),
that user gets ``is_admin=1``. Also honour ``app_settings.bootstrap_admin_email``.

Never accept or store seed phrases / private keys / chain passwords.
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
from mccc.security import SensitiveCredentialError, reject_sensitive_credential

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64
_HASH_PREFIX = "scrypt"

# Markers kept for introspection; enforcement goes through security.reject_sensitive_credential
SECRET_MARKERS = (
    "seed",
    "mnemonic",
    "private key",
    "privkey",
    "recovery phrase",
    "seed phrase",
    "2fa secret",
)

_SESSION_KEY = "mccc_user"
_SESSION_STORE: dict[str, Any] = {}  # process-local fallback for tests
_BOOTSTRAP_DONE = False


def _refuse_secrets(text: str) -> None:
    try:
        reject_sensitive_credential(text or "", field="auth")
    except SensitiveCredentialError as exc:
        raise ValueError(str(exc)) from exc


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


def _row_to_user(row: Any) -> Optional[dict[str, Any]]:
    if not row:
        return None
    user = dict(row)
    if user.get("deleted_at"):
        return None
    user.pop("password_hash", None)
    return user


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
        existing = conn.execute(
            "SELECT id, deleted_at FROM users WHERE email=?", (email_n,)
        ).fetchone()
        if existing and not existing["deleted_at"]:
            raise ValueError("Email already registered")
        if existing and existing["deleted_at"]:
            # Re-activate soft-deleted account with new credentials
            conn.execute(
                """UPDATE users SET password_hash=?, display_name=?, experience_level=?,
                   onboarding_goals=?, is_admin=?, deleted_at=NULL, updated_at=? WHERE id=?""",
                (
                    pw_hash,
                    (display_name or "").strip(),
                    (experience_level or "").strip(),
                    onboarding_goals or "",
                    1 if is_admin else 0,
                    now,
                    existing["id"],
                ),
            )
            user_id = int(existing["id"])
            # Ensure profile row
            prof = conn.execute(
                "SELECT user_id FROM profiles WHERE user_id=?", (user_id,)
            ).fetchone()
            if not prof:
                conn.execute(
                    """INSERT INTO profiles (user_id, theme, notify_prefs, created_at)
                       VALUES (?, 'dark', '{}', ?)""",
                    (user_id, now),
                )
            return user_id
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
        if not row or row["deleted_at"]:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return _row_to_user(row)


def get_user_by_id(user_id: int, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return _row_to_user(row)


def get_user_by_email(email: str, db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    email_n = _normalize_email(email)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email_n,)).fetchone()
        return _row_to_user(row)


def update_profile(
    user_id: int,
    *,
    display_name: Optional[str] = None,
    experience_level: Optional[str] = None,
    onboarding_goals: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Update profile fields. Refuses credential-like text."""
    updates: dict[str, Any] = {}
    if display_name is not None:
        _refuse_secrets(display_name)
        updates["display_name"] = display_name.strip()
    if experience_level is not None:
        _refuse_secrets(experience_level)
        updates["experience_level"] = experience_level.strip()
    if onboarding_goals is not None:
        _refuse_secrets(onboarding_goals)
        updates["onboarding_goals"] = onboarding_goals
    if not updates:
        user = get_user_by_id(user_id, db_path=db_path)
        if not user:
            raise ValueError("User not found")
        return user
    updates["updated_at"] = utc_now()
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [user_id]
    with connect(db_path) as conn:
        conn.execute(
            f"UPDATE users SET {cols} WHERE id=? AND deleted_at IS NULL",
            vals,
        )
    user = get_user_by_id(user_id, db_path=db_path)
    if not user:
        raise ValueError("User not found")
    return user


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db_path: Optional[Path] = None,
) -> None:
    """Change password with scrypt. Requires current password."""
    _refuse_secrets(new_password)
    if not new_password or len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters")
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row or row["deleted_at"]:
            raise ValueError("User not found")
        if not verify_password(current_password, row["password_hash"]):
            raise ValueError("Current password is incorrect")
        new_hash = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash=?, updated_at=? WHERE id=?",
            (new_hash, utc_now(), user_id),
        )


def delete_account(
    user_id: int,
    *,
    password: str = "",
    hard: bool = False,
    db_path: Optional[Path] = None,
) -> None:
    """Delete or soft-delete a user account.

    Default: soft-delete (``deleted_at`` set, password scrubbed) and remove
    user-scoped rows (profile, subscriptions, portfolio, watchlist, alerts,
    notifications, education progress, ai_usage for that user_id).
    Shared research data (projects/airdrops/wallets without user_id) is kept.
    """
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row or row["deleted_at"]:
            raise ValueError("User not found")
        if password:
            if not verify_password(password, row["password_hash"]):
                raise ValueError("Password is incorrect")
        # Cascade user-scoped rows carefully
        for sql in (
            "DELETE FROM profiles WHERE user_id=?",
            "DELETE FROM subscriptions WHERE user_id=?",
            "DELETE FROM portfolio_assets WHERE user_id=?",
            "DELETE FROM watchlist_items WHERE user_id=?",
            "DELETE FROM alerts WHERE user_id=?",
            "DELETE FROM notifications WHERE user_id=?",
            "DELETE FROM education_progress WHERE user_id=?",
            "DELETE FROM ai_usage WHERE user_id=?",
            "DELETE FROM bookmarks WHERE user_id=?",
        ):
            try:
                conn.execute(sql, (user_id,))
            except Exception:
                # Table may not have user_id or may not exist in older DBs
                pass
        if hard:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        else:
            # Soft-delete: scrub hash so login fails; keep email unique reserved
            scrub = hash_password(secrets.token_urlsafe(24))
            conn.execute(
                """UPDATE users SET password_hash=?, deleted_at=?, is_admin=0,
                   display_name='', onboarding_goals='', updated_at=? WHERE id=?""",
                (scrub, utc_now(), utc_now(), user_id),
            )
    # Clear session if this user was signed in
    current = get_session_user()
    if current and current.get("id") == user_id:
        clear_session_user()


def set_admin(user_id: int, is_admin: bool = True, db_path: Optional[Path] = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE users SET is_admin=?, updated_at=? WHERE id=? AND deleted_at IS NULL",
            (1 if is_admin else 0, utc_now(), user_id),
        )


def maybe_bootstrap_admin(db_path: Optional[Path] = None) -> Optional[int]:
    """Promote bootstrap email user to is_admin once per process (idempotent).

    Sources (first match):
    1. Env ``MCCC_BOOTSTRAP_ADMIN_EMAIL``
    2. ``app_settings.bootstrap_admin_email``
    Returns user_id if promoted or already admin, else None.
    """
    global _BOOTSTRAP_DONE
    email = os.environ.get("MCCC_BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    if not email:
        try:
            from mccc.db import get_setting

            email = (get_setting("bootstrap_admin_email", "", db_path=db_path) or "").strip().lower()
        except Exception:
            email = ""
    if not email:
        return None
    user = get_user_by_email(email, db_path=db_path)
    if not user:
        return None
    if user.get("is_admin"):
        _BOOTSTRAP_DONE = True
        return int(user["id"])
    set_admin(int(user["id"]), True, db_path=db_path)
    _BOOTSTRAP_DONE = True
    return int(user["id"])


# --- Session helpers (Streamlit-optional) ---


def _session_dict() -> dict[str, Any]:
    try:
        import streamlit as st  # type: ignore

        return st.session_state  # type: ignore[return-value]
    except Exception:
        return _SESSION_STORE


def set_session_user(user: dict[str, Any]) -> None:
    """Persist a safe user dict in session (password_hash stripped)."""
    safe = {k: v for k, v in user.items() if k != "password_hash"}
    _session_dict()[_SESSION_KEY] = safe


def clear_session_user() -> None:
    """Remove signed-in user from session (guest mode)."""
    store = _session_dict()
    if _SESSION_KEY in store:
        del store[_SESSION_KEY]


def get_session_user() -> Optional[dict[str, Any]]:
    """Return current session user or None. Guest mode is fully supported."""
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
        maybe_bootstrap_admin(db_path=db_path)
        # Refresh in case bootstrap flipped is_admin
        fresh = get_user_by_id(user["id"], db_path=db_path)
        if fresh:
            set_session_user(fresh)
            return fresh
    return user


def logout() -> None:
    """Clear session user. App continues in guest / single-user mode."""
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
