"""Public wallet watch helpers — never private keys / seeds / passwords."""
from __future__ import annotations

import os
import re
from typing import Any, Optional

import requests

from mccc.demo_data import DEMO_WALLET_BALANCES

ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
FORBIDDEN_MARKERS = ("private key", "seed phrase", "mnemonic", "password", "secret key")


def validate_public_address(address: str, chain: str = "ethereum") -> str:
    raw = (address or "").strip()
    lowered = raw.lower()
    for marker in FORBIDDEN_MARKERS:
        if marker in lowered:
            raise ValueError("Private keys, seed phrases, and passwords are never accepted.")
    if chain.lower() in ("ethereum", "arbitrum", "base", "optimism", "polygon"):
        if not ETH_ADDRESS_RE.match(raw):
            # Allow DEMO addresses for local practice
            if raw.startswith("0xDEMO"):
                return raw
            raise ValueError("Expected a public 0x… address (40 hex chars) or 0xDEMO… for demos.")
    if len(raw) < 8 or " " in raw:
        raise ValueError("Invalid public address")
    return raw


def fetch_eth_balance_wei(address: str, timeout: float = 8.0) -> tuple[Optional[float], str, bool]:
    """
    Try public Ethereum RPC / Etherscan. Returns (eth_amount, source, is_live).
    DEMO addresses always return DEMO balances.
    """
    if address.startswith("0xDEMO"):
        demo = DEMO_WALLET_BALANCES.get(address)
        if demo:
            eth = next((b["amount"] for b in demo["balances"] if b["token"] == "ETH"), 0.0)
            return eth, "DEMO balance table", False
        return 0.0, "DEMO (unknown demo address)", False

    api_key = os.environ.get("ETHERSCAN_API_KEY", "").strip()
    # Public Etherscan V2-style free endpoint (may require key); fall back gracefully
    try:
        if api_key:
            url = "https://api.etherscan.io/api"
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
                "apikey": api_key,
            }
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            if str(payload.get("status")) == "1":
                wei = int(payload["result"])
                return wei / 1e18, "Etherscan API", True
        # Cloudflare eth public RPC eth_getBalance
        rpc = "https://cloudflare-eth.com"
        body = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        }
        resp = requests.post(rpc, json=body, timeout=timeout)
        resp.raise_for_status()
        result = resp.json().get("result")
        if result:
            wei = int(result, 16)
            return wei / 1e18, "Cloudflare Ethereum gateway (public RPC)", True
    except Exception:
        pass

    return None, "DEMO fallback — public balance lookup unavailable", False


def balance_rows_for_address(address: str, chain: str = "ethereum") -> list[dict[str, Any]]:
    if address.startswith("0xDEMO") and address in DEMO_WALLET_BALANCES:
        return list(DEMO_WALLET_BALANCES[address]["balances"])

    eth, source, is_live = fetch_eth_balance_wei(address)
    if eth is None:
        return [
            {
                "token": "ETH",
                "amount": 0.0,
                "usd_value": None,
                "source": source,
                "is_live": False,
            }
        ]
    return [
        {
            "token": "ETH" if chain.lower() in ("ethereum", "arbitrum", "base", "optimism") else chain.upper(),
            "amount": round(eth, 6),
            "usd_value": None,
            "source": source,
            "is_live": is_live,
        }
    ]
