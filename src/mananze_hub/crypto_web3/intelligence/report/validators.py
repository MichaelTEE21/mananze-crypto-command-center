"""Input validation and entity detection for Intelligence Reports.

Public addresses only. Rejects secrets. Explains unsupported inputs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from mccc.intelligence.report.schema import EntityType, SUPPORTED_ENTITY_TYPES
from mccc.security import SensitiveCredentialError, reject_sensitive_credential

ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
DEMO_ADDRESS_RE = re.compile(r"^0xDEMO[0-9A-Za-z]{0,36}$", re.IGNORECASE)
# Contract addresses on EVM look like wallets; we distinguish via hint/entity_type.
SOL_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
TOKEN_SYMBOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-.]{1,20}$")

KNOWN_TOKEN_ALIASES = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "usdc": "usd-coin",
    "usdt": "tether",
}

KNOWN_PROTOCOL_HINTS = {
    "uniswap",
    "aave",
    "lido",
    "curve",
    "compound",
    "makerdao",
    "maker",
    "eigenlayer",
    "pendle",
}


@dataclass
class ValidatedQuery:
    ok: bool
    query: str
    entity_type: str
    chain: str
    normalized: str
    error: str = ""
    warnings: list[str] | None = None
    rejected_secret: bool = False

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


def _clean(text: str) -> str:
    return " ".join((text or "").strip().split())


def detect_entity_type(query: str, hint: Optional[str] = None) -> str:
    """Best-effort detection. Prefer explicit hint when valid."""
    h = (hint or "").strip().lower()
    if h in SUPPORTED_ENTITY_TYPES:
        return h
    q = _clean(query)
    ql = q.lower()
    if not q:
        return EntityType.UNKNOWN.value
    if ql.startswith("rwa:") or ql.startswith("rwa "):
        return EntityType.RWA.value
    if DEMO_ADDRESS_RE.match(q) or ETH_ADDRESS_RE.match(q):
        if h == EntityType.CONTRACT.value:
            return EntityType.CONTRACT.value
        return EntityType.WALLET.value
    if ql in KNOWN_TOKEN_ALIASES or (TOKEN_SYMBOL_RE.match(q) and len(q) <= 10 and q.isupper()):
        return EntityType.TOKEN.value
    if ql in KNOWN_TOKEN_ALIASES or ql in ("bitcoin", "ethereum", "solana", "usd-coin", "tether"):
        return EntityType.TOKEN.value
    if ql in KNOWN_PROTOCOL_HINTS or ql.startswith("protocol:"):
        return EntityType.PROTOCOL.value
    if ql.startswith("token:"):
        return EntityType.TOKEN.value
    if ql.startswith("project:"):
        return EntityType.PROJECT.value
    if ql.startswith("contract:"):
        return EntityType.CONTRACT.value
    if ql.startswith("wallet:") or ql.startswith("address:"):
        return EntityType.WALLET.value
    # Default research entity: project name search
    return EntityType.PROJECT.value


def strip_prefix(query: str) -> str:
    q = _clean(query)
    for prefix in (
        "rwa:",
        "rwa ",
        "token:",
        "project:",
        "protocol:",
        "contract:",
        "wallet:",
        "address:",
    ):
        if q.lower().startswith(prefix):
            return _clean(q[len(prefix) :])
    return q


def validate_report_query(
    query: str,
    *,
    entity_type_hint: Optional[str] = None,
    chain: str = "ethereum",
) -> ValidatedQuery:
    """Validate user input for Intelligence Report analysis."""
    warnings: list[str] = []
    raw = _clean(query)
    if not raw:
        return ValidatedQuery(
            ok=False,
            query="",
            entity_type=EntityType.UNKNOWN.value,
            chain=chain,
            normalized="",
            error="Enter a project, token, public wallet address, protocol, contract, or RWA name to analyse.",
        )

    try:
        reject_sensitive_credential(raw, field="report.query")
    except SensitiveCredentialError as exc:
        return ValidatedQuery(
            ok=False,
            query=raw,
            entity_type=EntityType.UNSUPPORTED.value,
            chain=chain,
            normalized="",
            error=str(exc),
            rejected_secret=True,
        )

    # Also reject if any whitespace-separated chunk looks like a hex private key alone
    for part in raw.split():
        try:
            reject_sensitive_credential(part, field="report.query.part")
        except SensitiveCredentialError as exc:
            return ValidatedQuery(
                ok=False,
                query=raw,
                entity_type=EntityType.UNSUPPORTED.value,
                chain=chain,
                normalized="",
                error=str(exc),
                rejected_secret=True,
            )

    hint = (entity_type_hint or "").strip().lower() or None
    if hint and hint not in SUPPORTED_ENTITY_TYPES and hint not in ("auto", "", "unknown"):
        return ValidatedQuery(
            ok=False,
            query=raw,
            entity_type=EntityType.UNSUPPORTED.value,
            chain=chain,
            normalized=strip_prefix(raw),
            error=(
                f"Unsupported entity type `{hint}`. Supported: "
                + ", ".join(sorted(SUPPORTED_ENTITY_TYPES))
                + "."
            ),
        )

    entity = detect_entity_type(raw, hint=None if hint in (None, "auto") else hint)
    normalized = strip_prefix(raw)
    ch = (chain or "ethereum").strip().lower() or "ethereum"

    if entity == EntityType.WALLET.value or entity == EntityType.CONTRACT.value:
        from mccc.wallets import validate_public_address

        try:
            # Solana-style: allow through wallets.validate only for EVM; handle SOL lightly
            if ch == "solana":
                if not (SOL_ADDRESS_RE.match(normalized) or normalized.startswith("0xDEMO")):
                    return ValidatedQuery(
                        ok=False,
                        query=raw,
                        entity_type=entity,
                        chain=ch,
                        normalized=normalized,
                        error="Expected a public Solana address or 0xDEMO… for demos.",
                    )
            else:
                normalized = validate_public_address(normalized, chain=ch)
        except ValueError as exc:
            return ValidatedQuery(
                ok=False,
                query=raw,
                entity_type=entity,
                chain=ch,
                normalized=normalized,
                error=str(exc),
            )
        if entity == EntityType.CONTRACT.value:
            warnings.append(
                "Contract vs wallet: EVM addresses look alike. Analysis treats this as a contract "
                "hint only — identity claims require verified authoritative sources."
            )

    if entity == EntityType.TOKEN.value:
        key = normalized.lower()
        if key in KNOWN_TOKEN_ALIASES:
            normalized = KNOWN_TOKEN_ALIASES[key]
        elif not TOKEN_SYMBOL_RE.match(normalized.replace(" ", "-")) and len(normalized) < 2:
            return ValidatedQuery(
                ok=False,
                query=raw,
                entity_type=entity,
                chain=ch,
                normalized=normalized,
                error="Token query too short or invalid.",
            )

    if entity == EntityType.UNSUPPORTED.value:
        return ValidatedQuery(
            ok=False,
            query=raw,
            entity_type=entity,
            chain=ch,
            normalized=normalized,
            error="This input is not a supported on-chain entity for Intelligence Reports.",
        )

    return ValidatedQuery(
        ok=True,
        query=raw,
        entity_type=entity,
        chain=ch,
        normalized=normalized,
        warnings=warnings,
    )
