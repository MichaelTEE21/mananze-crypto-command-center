"""Solana explorer — public RPC balance; tx UNAVAILABLE without dedicated keyed API."""
from __future__ import annotations

from typing import Any

import requests

from mccc.explorers.base import (
    DATA_UNAVAILABLE,
    ExplorerProvider,
    ExplorerResult,
    ExplorerStatus,
    register_provider,
)
from mccc.security import SensitiveCredentialError, reject_sensitive_credential

_PUBLIC_RPC = "https://api.mainnet-beta.solana.com"


class SolanaExplorer(ExplorerProvider):
    chain = "solana"
    display_name = "Solana"

    def available(self) -> bool:
        return True

    def lookup_address(self, address: str) -> ExplorerResult:
        raw = (address or "").strip()
        try:
            reject_sensitive_credential(raw, field="explorer.address")
        except SensitiveCredentialError as exc:
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query="",
                status=ExplorerStatus.UNAVAILABLE,
                source="security",
                summary=str(exc),
                label="UNAVAILABLE",
            )
        if len(raw) < 32 or " " in raw:
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw[:64],
                status=ExplorerStatus.UNAVAILABLE,
                source="validation",
                summary="Invalid Solana address shape",
                label="UNAVAILABLE",
            )
        try:
            resp = requests.post(
                _PUBLIC_RPC,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [raw],
                },
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("error"):
                return ExplorerResult(
                    chain=self.chain,
                    kind="address",
                    query=raw,
                    status=ExplorerStatus.UNAVAILABLE,
                    source="solana-mainnet-beta",
                    summary=DATA_UNAVAILABLE,
                    label="UNAVAILABLE",
                    fields={"error": payload["error"]},
                )
            lamports = int((payload.get("result") or {}).get("value") or 0)
            sol = lamports / 1e9
            fields: dict[str, Any] = {
                "address": raw,
                "lamports": lamports,
                "sol": sol,
                "sol_label": "CALCULATED",
            }
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw,
                status=ExplorerStatus.VERIFIED,
                source="solana public RPC",
                summary=f"Balance {sol} SOL [VERIFIED lamports; CALCULATED SOL]",
                label="VERIFIED",
                fields=fields,
            )
        except Exception as exc:  # noqa: BLE001
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw,
                status=ExplorerStatus.UNAVAILABLE,
                source="solana-mainnet-beta",
                summary=f"{DATA_UNAVAILABLE} ({type(exc).__name__})",
                label="UNAVAILABLE",
            )

    def lookup_tx(self, tx_hash: str) -> ExplorerResult:
        raw = (tx_hash or "").strip()
        try:
            reject_sensitive_credential(raw, field="explorer.tx")
        except SensitiveCredentialError as exc:
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query="",
                status=ExplorerStatus.UNAVAILABLE,
                source="security",
                summary=str(exc),
                label="UNAVAILABLE",
            )
        # Public getTransaction often rate-limits / needs commitment tuning —
        # keep honest UNAVAILABLE rather than inventing.
        return ExplorerResult(
            chain=self.chain,
            kind="tx",
            query=raw,
            status=ExplorerStatus.UNAVAILABLE,
            source="solana",
            summary=f"{DATA_UNAVAILABLE} — Solana tx decode not wired (use Solscan)",
            label="UNAVAILABLE",
            fields={"signature": raw, "hint": "https://solscan.io/"},
        )


def register() -> None:
    register_provider(SolanaExplorer())
