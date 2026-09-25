"""Bitcoin explorer — public address balance via mempool.space; tx when reachable."""
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


class BitcoinExplorer(ExplorerProvider):
    chain = "bitcoin"
    display_name = "Bitcoin"

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
        if len(raw) < 26 or " " in raw:
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw[:64],
                status=ExplorerStatus.UNAVAILABLE,
                source="validation",
                summary="Invalid Bitcoin address shape",
                label="UNAVAILABLE",
            )
        try:
            resp = requests.get(f"https://mempool.space/api/address/{raw}", timeout=10)
            if resp.status_code == 404:
                return ExplorerResult(
                    chain=self.chain,
                    kind="address",
                    query=raw,
                    status=ExplorerStatus.UNAVAILABLE,
                    source="mempool.space",
                    summary=DATA_UNAVAILABLE,
                    label="UNAVAILABLE",
                )
            resp.raise_for_status()
            data = resp.json()
            chain_stats = data.get("chain_stats") or {}
            funded = int(chain_stats.get("funded_txo_sum") or 0)
            spent = int(chain_stats.get("spent_txo_sum") or 0)
            balance_sats = funded - spent
            balance_btc = balance_sats / 1e8
            fields: dict[str, Any] = {
                "address": raw,
                "balance_sats": balance_sats,
                "balance_btc": balance_btc,
                "tx_count": chain_stats.get("tx_count"),
                "balance_btc_label": "CALCULATED",
            }
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw,
                status=ExplorerStatus.VERIFIED,
                source="mempool.space",
                summary=f"Balance {balance_btc} BTC [VERIFIED sats; CALCULATED BTC]",
                label="VERIFIED",
                fields=fields,
            )
        except Exception as exc:  # noqa: BLE001
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw,
                status=ExplorerStatus.UNAVAILABLE,
                source="mempool.space",
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
        if len(raw) < 64:
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw[:80],
                status=ExplorerStatus.UNAVAILABLE,
                source="validation",
                summary="Expected a Bitcoin txid",
                label="UNAVAILABLE",
            )
        try:
            resp = requests.get(f"https://mempool.space/api/tx/{raw}", timeout=10)
            if resp.status_code == 404:
                return ExplorerResult(
                    chain=self.chain,
                    kind="tx",
                    query=raw,
                    status=ExplorerStatus.UNAVAILABLE,
                    source="mempool.space",
                    summary=DATA_UNAVAILABLE,
                    label="UNAVAILABLE",
                )
            resp.raise_for_status()
            data = resp.json()
            fields = {
                "txid": data.get("txid") or raw,
                "fee": data.get("fee"),
                "size": data.get("size"),
                "status": data.get("status"),
            }
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw,
                status=ExplorerStatus.VERIFIED,
                source="mempool.space",
                summary="Transaction found [VERIFIED]",
                label="VERIFIED",
                fields=fields,
            )
        except Exception as exc:  # noqa: BLE001
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw,
                status=ExplorerStatus.UNAVAILABLE,
                source="mempool.space",
                summary=f"{DATA_UNAVAILABLE} ({type(exc).__name__})",
                label="UNAVAILABLE",
            )


def register() -> None:
    register_provider(BitcoinExplorer())
