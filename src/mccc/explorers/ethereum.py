"""Ethereum public explorer — balance via existing wallets helpers; tx via Etherscan when keyed."""
from __future__ import annotations

import os
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


class EthereumExplorer(ExplorerProvider):
    chain = "ethereum"
    display_name = "Ethereum"

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
        from mccc.wallets import balance_rows_for_address, validate_public_address

        try:
            addr = validate_public_address(raw, chain="ethereum")
        except ValueError as exc:
            return ExplorerResult(
                chain=self.chain,
                kind="address",
                query=raw[:64],
                status=ExplorerStatus.UNAVAILABLE,
                source="validation",
                summary=str(exc),
                label="UNAVAILABLE",
            )
        rows = balance_rows_for_address(addr, chain="ethereum")
        row = rows[0] if rows else {}
        is_live = bool(row.get("is_live"))
        is_demo = addr.startswith("0xDEMO") or not is_live
        status = ExplorerStatus.DEMO if is_demo else ExplorerStatus.VERIFIED
        label = "DEMO" if is_demo else "VERIFIED"
        eth_amt = row.get("amount")
        fields: dict[str, Any] = {
            "address": addr,
            "native_symbol": "ETH",
            "native_balance": eth_amt,
            "is_live": is_live,
        }
        return ExplorerResult(
            chain=self.chain,
            kind="address",
            query=addr,
            status=status,
            source=str(row.get("source") or "unknown"),
            summary=f"ETH balance={eth_amt} · {label}",
            label=label,
            fields=fields,
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
        if not raw.startswith("0x") or len(raw) < 66:
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw[:80],
                status=ExplorerStatus.UNAVAILABLE,
                source="validation",
                summary="Expected a 0x… transaction hash",
                label="UNAVAILABLE",
            )
        api_key = os.environ.get("ETHERSCAN_API_KEY", "").strip()
        if not api_key:
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw,
                status=ExplorerStatus.UNAVAILABLE,
                source="etherscan",
                summary=f"{DATA_UNAVAILABLE} — set ETHERSCAN_API_KEY for tx lookup",
                label="UNAVAILABLE",
                fields={"tx_hash": raw},
            )
        try:
            resp = requests.get(
                "https://api.etherscan.io/api",
                params={
                    "module": "proxy",
                    "action": "eth_getTransactionByHash",
                    "txhash": raw,
                    "apikey": api_key,
                },
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            result = payload.get("result")
            if not result:
                return ExplorerResult(
                    chain=self.chain,
                    kind="tx",
                    query=raw,
                    status=ExplorerStatus.UNAVAILABLE,
                    source="etherscan",
                    summary=DATA_UNAVAILABLE,
                    label="UNAVAILABLE",
                    fields={"tx_hash": raw, "raw_status": payload.get("message")},
                )
            # CALCULATED: wei → ETH display
            value_wei = int(result.get("value") or "0x0", 16)
            value_eth = value_wei / 1e18
            fields = {
                "tx_hash": raw,
                "from": result.get("from"),
                "to": result.get("to"),
                "blockNumber": result.get("blockNumber"),
                "value_wei": value_wei,
                "value_eth": value_eth,
            }
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw,
                status=ExplorerStatus.VERIFIED,
                source="Etherscan API",
                summary=f"Tx found · value_eth={value_eth} [VERIFIED]; ETH conversion [CALCULATED]",
                label="VERIFIED",
                fields={**fields, "value_eth_label": "CALCULATED"},
            )
        except Exception as exc:  # noqa: BLE001
            return ExplorerResult(
                chain=self.chain,
                kind="tx",
                query=raw,
                status=ExplorerStatus.UNAVAILABLE,
                source="etherscan",
                summary=f"{DATA_UNAVAILABLE} ({type(exc).__name__})",
                label="UNAVAILABLE",
                fields={"tx_hash": raw},
            )


def register() -> None:
    register_provider(EthereumExplorer())
