"""Central credential / secret rejection for MCCC.

Never accept or store seed phrases, private keys, exchange/wallet passwords, or 2FA secrets.
Call reject_sensitive_credential() on free-text fields (wallet address, notes, passwords, AI input).
"""
from __future__ import annotations

import re
from typing import Optional

# BIP39-ish: 12 or 24 space-separated words (letters only, typical mnemonic shape)
_MNEMONIC_RE = re.compile(
    r"^(?:[a-z]+(?:\s+[a-z]+){11}|(?:[a-z]+(?:\s+[a-z]+){23}))$",
    re.IGNORECASE,
)

# Hex private key: 64 hex chars, optional 0x prefix (not a 40-char address)
_HEX_PRIVKEY_RE = re.compile(r"^(?:0x)?[a-fA-F0-9]{64}$")

# Explicit marker phrases (substring match on lowered text)
_MARKER_PHRASES = (
    "private key",
    "privkey",
    "seed phrase",
    "recovery phrase",
    "secret key",
    "mnemonic",
    "wallet password",
    "exchange password",
    "2fa secret",
    "2fa code",
    "authenticator secret",
    "otp secret",
    "backup phrase",
    "secret recovery",
)

# Lone keyword hits that are strong signals when the field is short or key-like
_STRONG_KEYWORDS = (
    "mnemonic",
    "privkey",
    "privatekey",
)

DEFAULT_MESSAGE = (
    "Sensitive credentials are not allowed. "
    "MCCC never accepts seed phrases, private keys, wallet/exchange passwords, or 2FA secrets."
)


class SensitiveCredentialError(ValueError):
    """Raised when input looks like a secret that must not be stored."""


def looks_like_mnemonic(text: str) -> bool:
    """True if text is exactly 12 or 24 space-separated alphabetic words."""
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return False
    return bool(_MNEMONIC_RE.match(cleaned))


def looks_like_hex_private_key(text: str) -> bool:
    """True for 64-hex (optional 0x) strings — distinct from 40-char public addresses."""
    cleaned = (text or "").strip()
    if not cleaned:
        return False
    # Public ETH addresses are 40 hex chars after 0x — allow those through this check
    if re.match(r"^0x[a-fA-F0-9]{40}$", cleaned):
        return False
    return bool(_HEX_PRIVKEY_RE.match(cleaned))


def contains_credential_markers(text: str) -> bool:
    lowered = (text or "").lower()
    if not lowered.strip():
        return False
    for phrase in _MARKER_PHRASES:
        if phrase in lowered:
            return True
    compact = re.sub(r"[\s_-]+", "", lowered)
    for kw in _STRONG_KEYWORDS:
        if kw in compact:
            return True
    return False


def is_sensitive_credential(text: str) -> bool:
    """Return True if text should be rejected as a credential-like secret."""
    if text is None:
        return False
    raw = str(text)
    if not raw.strip():
        return False
    if contains_credential_markers(raw):
        return True
    if looks_like_mnemonic(raw):
        return True
    if looks_like_hex_private_key(raw):
        return True
    return False


def reject_sensitive_credential(
    text: str,
    *,
    field: str = "input",
    message: Optional[str] = None,
) -> str:
    """Validate text; raise SensitiveCredentialError if credential-like.

    Returns the original text unchanged when safe (so callers can chain).
    """
    if is_sensitive_credential(text):
        msg = message or f"{DEFAULT_MESSAGE} (field: {field})"
        raise SensitiveCredentialError(msg)
    return text
