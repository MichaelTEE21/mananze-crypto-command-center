"""Public donation address config for Support MCCC.

Addresses are public (not secrets). Prefer env; fall back to documented defaults.
Never invent donation totals / "raised" stats.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Documented public defaults (user-provided). Safe to ship in repo.
DEFAULT_BTC = "bc1q7a9uh6utn85gjhs5dakn3kkazsmt9s4q37cn32"
DEFAULT_ETH = "0x6d04cff44c379cb89050ddb9b55e3b29d3ffc091"
DEFAULT_SOL = "BgQgsr63rbRNsjLabU5toVwj1itkfLDHMLxCCo29tCwB"

ENV_BTC = "MCCC_BTC_DONATION_ADDRESS"
ENV_ETH = "MCCC_ETH_DONATION_ADDRESS"
ENV_SOL = "MCCC_SOL_DONATION_ADDRESS"

DONATION_WARNING = (
    "Verify network and asset before sending. "
    "Never share seed phrases, private keys, or wallet passwords. "
    "MCCC never asks for recovery phrases. Donations are voluntary and not a purchase of PRO."
)


@dataclass(frozen=True)
class DonationChannel:
    asset: str
    network: str
    address: str
    env_key: str
    from_env: bool
    explorer_hint: str


def _read_address(env_key: str, default: str) -> tuple[str, bool]:
    raw = os.environ.get(env_key, "").strip()
    if raw:
        return raw, True
    return default, False


def get_donation_channels() -> list[DonationChannel]:
    """Return BTC / ETH / SOL channels (env override or documented defaults)."""
    btc, btc_env = _read_address(ENV_BTC, DEFAULT_BTC)
    eth, eth_env = _read_address(ENV_ETH, DEFAULT_ETH)
    sol, sol_env = _read_address(ENV_SOL, DEFAULT_SOL)
    return [
        DonationChannel(
            asset="BTC",
            network="Bitcoin",
            address=btc,
            env_key=ENV_BTC,
            from_env=btc_env,
            explorer_hint="https://mempool.space/",
        ),
        DonationChannel(
            asset="ETH",
            network="Ethereum",
            address=eth,
            env_key=ENV_ETH,
            from_env=eth_env,
            explorer_hint="https://etherscan.io/",
        ),
        DonationChannel(
            asset="SOL",
            network="Solana",
            address=sol,
            env_key=ENV_SOL,
            from_env=sol_env,
            explorer_hint="https://solscan.io/",
        ),
    ]


def get_channel(asset: str) -> Optional[DonationChannel]:
    key = (asset or "").strip().upper()
    for ch in get_donation_channels():
        if ch.asset == key:
            return ch
    return None


def address_for(asset: str) -> str:
    ch = get_channel(asset)
    if not ch:
        raise ValueError(f"Unknown donation asset: {asset}")
    return ch.address


def qr_png_bytes(payload: str, *, box_size: int = 6, border: int = 2) -> bytes:
    """Encode exact address string as QR PNG bytes. Requires qrcode[+pil]."""
    import io

    import qrcode

    img = qrcode.make(payload, box_size=box_size, border=border)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- Support prompt (first-visit, delayed, never annoying) ---

SESSION_DISMISSED_KEY = "_mccc_donate_dismissed"
SESSION_SEEN_HOME_KEY = "_mccc_donate_seen_home"
SESSION_PROMPT_SHOWN_KEY = "_mccc_donate_prompt_shown"
SESSION_HOME_RUNS_KEY = "_mccc_donate_home_runs"
PREF_DISMISS_KEY = "donate_prompt_dismissed"  # durable user preference when authed

# Show soft prompt only after user has had a chance to explore (N home reruns / interactions)
DELAY_HOME_INTERACTIONS = 2


def is_donate_prompt_dismissed(*, user_id=None) -> bool:
    """Session dismiss OR durable preference (signed-in)."""
    try:
        import streamlit as st

        if st.session_state.get(SESSION_DISMISSED_KEY):
            return True
    except Exception:
        pass
    if user_id is not None:
        try:
            from mccc.db import get_setting

            # per-user preference stored as app_settings key
            val = get_setting(f"user:{int(user_id)}:{PREF_DISMISS_KEY}", "")
            if str(val).strip() in ("1", "true", "True", "yes"):
                return True
        except Exception:
            pass
    return False


def dismiss_donate_prompt(*, user_id=None, durable: bool = True) -> None:
    """Dismiss for this session; optionally persist for signed-in users."""
    try:
        import streamlit as st

        st.session_state[SESSION_DISMISSED_KEY] = True
        st.session_state[SESSION_PROMPT_SHOWN_KEY] = True
    except Exception:
        pass
    if durable and user_id is not None:
        try:
            from mccc.db import set_setting

            set_setting(f"user:{int(user_id)}:{PREF_DISMISS_KEY}", "1")
        except Exception:
            pass


def should_show_donate_soft_prompt(page_key: str, *, user_id=None) -> bool:
    """First-visit soft prompt on Command Center only — delayed, never every navigation.

    Rules:
    - Only on command_center
    - Not if session or durable dismissed
    - Not if already shown this session
    - Delayed: require DELAY_HOME_INTERACTIONS home runs so user can explore first
    """
    if page_key != "command_center":
        return False
    if is_donate_prompt_dismissed(user_id=user_id):
        return False
    try:
        import streamlit as st
    except Exception:
        return False

    runs = int(st.session_state.get(SESSION_HOME_RUNS_KEY) or 0) + 1
    st.session_state[SESSION_HOME_RUNS_KEY] = runs
    st.session_state[SESSION_SEEN_HOME_KEY] = True

    if st.session_state.get(SESSION_PROMPT_SHOWN_KEY):
        return False
    if runs < DELAY_HOME_INTERACTIONS:
        return False
    return True
