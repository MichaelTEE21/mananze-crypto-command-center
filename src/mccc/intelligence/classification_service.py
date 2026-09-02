"""CLASSIFY stage — rule-based category + subcategory. No invented facts."""
from __future__ import annotations

import re
from typing import Optional

from mccc.intelligence.schema import EventCategory, RawDocument
from mccc.intelligence.rwa.classification import RWAClassificationService


_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (
        EventCategory.RWA.value,
        [
            re.compile(r"\b(rwa|real[\s-]?world\s+asset|tokeniz(?:e|ed|ation)|tokenized\s+(?:treasury|treasuries|real\s+estate|credit|gold|bond|fund))\b", re.I),
            re.compile(r"\b(private\s+credit|on[\s-]?chain\s+treasury|t[\s-]?bill)\b", re.I),
        ],
    ),
    (
        EventCategory.FUNDING.value,
        [
            re.compile(r"\b(funding|raises?|series\s+[a-d]|seed round|venture|led by)\b", re.I),
        ],
    ),
    (
        EventCategory.AIRDROP_SIGNALS.value,
        [
            re.compile(r"\b(airdrop|points?\s+program|season\s+\d+|claim\s+portal|eligibility)\b", re.I),
        ],
    ),
    (
        EventCategory.TOKEN_EVENTS.value,
        [
            re.compile(r"\b(token\s+unlock|vesting|tge|listing|token\s+generation)\b", re.I),
        ],
    ),
    (
        EventCategory.NEW_PROJECTS.value,
        [
            re.compile(r"\b(launches?|introduc(?:e|ing)|new\s+protocol|open[\s-]?source\s+toolkit)\b", re.I),
        ],
    ),
    (
        EventCategory.TECHNOLOGY.value,
        [
            re.compile(r"\b(upgrade|mainnet|testnet|zk|rollup|eip[-\s]?\d+|client\s+release)\b", re.I),
        ],
    ),
    (
        EventCategory.BREAKING.value,
        [
            re.compile(r"\b(breaking|halted|outage|exploit|hacked|emergency|congestion\s+advisory)\b", re.I),
        ],
    ),
    (
        EventCategory.NARRATIVES.value,
        [
            re.compile(r"\b(narrative|thesis|sector\s+rotation|meta|trend(?:ing)?)\b", re.I),
        ],
    ),
]


class ClassificationService:
    def __init__(self) -> None:
        self._rwa = RWAClassificationService()

    def classify(self, doc: RawDocument) -> tuple[str, str]:
        """Return (category, subcategory). Prefer meta hint if valid; else rules; else technology."""
        hint = str((doc.meta or {}).get("category_hint") or "").strip().lower()
        valid = {c.value for c in EventCategory}
        rwa = self._rwa.classify(doc)
        sub_hint = str((doc.meta or {}).get("subcategory") or "").strip()
        if hint in valid:
            if hint == EventCategory.RWA.value:
                sub = sub_hint or rwa.rwa_category or str((doc.meta or {}).get("rwa_category") or "")
                return hint, sub
            return hint, sub_hint
        # RWA membership wins over generic technology when signals fire
        if rwa.is_rwa:
            return EventCategory.RWA.value, rwa.rwa_category or sub_hint
        blob = f"{doc.title}\n{doc.body}"
        for category, patterns in _RULES:
            for pat in patterns:
                if pat.search(blob):
                    if category == EventCategory.RWA.value:
                        return category, rwa.rwa_category or sub_hint
                    return category, sub_hint
        return EventCategory.TECHNOLOGY.value, ""
