"""EXTRACT stage — pull project/token/chain/entities from text without inventing facts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from mccc.intelligence.schema import (
    AirdropSignalStatus,
    NOT_DISCLOSED,
    UNKNOWN,
    UNCONFIRMED_LABEL,
    RawDocument,
)


_TOKEN_RE = re.compile(r"\$([A-Z]{2,10})\b")
_CHAIN_HINTS = {
    "ethereum": "ethereum",
    "eth ": "ethereum",
    "solana": "solana",
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
    "base ": "base",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
    "cosmos": "cosmos",
}


@dataclass
class ExtractionResult:
    project: str = UNKNOWN
    token: str = UNKNOWN
    blockchain: str = UNKNOWN
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    funding_amount: str = NOT_DISCLOSED
    airdrop_signal_status: str = ""
    investors: list[str] = field(default_factory=list)


class ExtractionService:
    """Deterministic extractors — unknown stays Unknown / Not disclosed / Unconfirmed."""

    def extract(self, doc: RawDocument, category: str = "") -> ExtractionResult:
        meta = doc.meta or {}
        project = str(meta.get("project") or "").strip() or self._guess_project(doc.title)
        token = str(meta.get("token") or "").strip() or self._guess_token(doc.title, doc.body)
        blockchain = str(meta.get("blockchain") or "").strip() or self._guess_chain(doc.title, doc.body)
        tags = list(meta.get("tags") or [])
        if doc.is_demo and "demo" not in [t.lower() for t in tags]:
            tags = ["demo"] + tags
        entities: list[str] = []
        for val in (project, token, blockchain):
            if val and val not in (UNKNOWN, NOT_DISCLOSED, UNCONFIRMED_LABEL) and val not in entities:
                entities.append(val)
        funding_amount = str(meta.get("funding_amount") or NOT_DISCLOSED)
        # Never invent a dollar amount from prose in P1
        if category == "funding" and funding_amount == NOT_DISCLOSED:
            funding_amount = NOT_DISCLOSED
        airdrop_status = str(meta.get("airdrop_signal_status") or "")
        if category == "airdrop_signals" and not airdrop_status:
            airdrop_status = AirdropSignalStatus.UNCONFIRMED.value
        # investors: only from meta — never invent names
        investors_raw = meta.get("investors")
        investors: list[str] = []
        if isinstance(investors_raw, list):
            investors = [str(x).strip() for x in investors_raw if str(x).strip()]
        elif isinstance(investors_raw, str) and investors_raw.strip():
            investors = [investors_raw.strip()]
        return ExtractionResult(
            project=project or UNKNOWN,
            token=token or UNKNOWN,
            blockchain=blockchain or UNKNOWN,
            entities=entities,
            tags=tags,
            funding_amount=funding_amount,
            airdrop_signal_status=airdrop_status,
            investors=investors,
        )

    def _guess_project(self, title: str) -> str:
        # Only use explicit DEMO- Name patterns or leave Unknown — do not invent brands
        m = re.search(r"\b(DEMO-[A-Za-z0-9]+)\b", title or "")
        if m:
            return m.group(1)
        return UNKNOWN

    def _guess_token(self, title: str, body: str) -> str:
        m = _TOKEN_RE.search(f"{title} {body}")
        if m:
            return m.group(1)
        if re.search(r"\bDEMO\b", title or ""):
            return UNKNOWN
        return UNKNOWN

    def _guess_chain(self, title: str, body: str) -> str:
        blob = f"{title} {body}".lower()
        for needle, chain in _CHAIN_HINTS.items():
            if needle in blob:
                return chain
        return UNKNOWN
