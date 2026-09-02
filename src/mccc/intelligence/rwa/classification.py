"""RWA classification + signal detection — extends Intelligence Agent rules."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from mccc.intelligence.rwa.taxonomy import (
    RWACategory,
    RWAEventType,
    is_known_rwa_category,
)
from mccc.intelligence.schema import RawDocument


# Broad RWA membership signals
_RWA_MEMBERSHIP = [
    re.compile(r"\b(rwa|real[\s-]?world\s+asset|tokeniz(?:e|ed|ation)|on[\s-]?chain\s+(?:treasury|bond|credit|real\s+estate))\b", re.I),
    re.compile(r"\b(treasury\s+bill|t[\s-]?bill|private\s+credit|tokenized\s+(?:fund|gold|commodity|real\s+estate))\b", re.I),
    re.compile(r"\b(blackrock|franklin\s+templeton|ondo|centrifuge|maple\s+finance|securitize|polymesh)\b", re.I),
]

_CATEGORY_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (RWACategory.TOKENIZED_TREASURIES.value, [re.compile(r"\b(treasury|t[\s-]?bill|usdt[b]|budl|ousg)\b", re.I)]),
    (RWACategory.REAL_ESTATE.value, [re.compile(r"\b(real\s+estate|property|reit|tokenized\s+property)\b", re.I)]),
    (RWACategory.PRIVATE_CREDIT.value, [re.compile(r"\b(private\s+credit|credit\s+fund|loan\s+pool)\b", re.I)]),
    (RWACategory.CORPORATE_CREDIT.value, [re.compile(r"\b(corporate\s+credit|corporate\s+bond)\b", re.I)]),
    (RWACategory.CONSUMER_CREDIT.value, [re.compile(r"\b(consumer\s+credit|consumer\s+loan)\b", re.I)]),
    (RWACategory.COMMODITIES.value, [re.compile(r"\b(commodit(?:y|ies)|tokenized\s+oil|wheat\s+token)\b", re.I)]),
    (RWACategory.GOLD_PRECIOUS_METALS.value, [re.compile(r"\b(gold|silver|precious\s+metal|paxg|xaut)\b", re.I)]),
    (RWACategory.AGRICULTURE.value, [re.compile(r"\b(agriculture|agri[\s-]?finance|farmland)\b", re.I)]),
    (RWACategory.TRADE_FINANCE.value, [re.compile(r"\b(trade\s+finance|invoice\s+factoring|letter\s+of\s+credit)\b", re.I)]),
    (RWACategory.INFRASTRUCTURE.value, [re.compile(r"\b(infrastructure\s+(?:token|fund)|infra\s+rwa)\b", re.I)]),
    (RWACategory.ENERGY.value, [re.compile(r"\b(energy\s+(?:token|asset)|tokenized\s+energy)\b", re.I)]),
    (RWACategory.FUNDS.value, [re.compile(r"\b(tokenized\s+fund|fund\s+tokenization)\b", re.I)]),
    (RWACategory.SECURITIES.value, [re.compile(r"\b(security\s+token|tokenized\s+securit)\b", re.I)]),
    (RWACategory.BONDS.value, [re.compile(r"\b(tokenized\s+bond|on[\s-]?chain\s+bond)\b", re.I)]),
    (RWACategory.STABLECOINS.value, [re.compile(r"\b(stablecoin|fiat[\s-]?backed)\b", re.I)]),
    (RWACategory.CARBON_ENVIRONMENTAL.value, [re.compile(r"\b(carbon\s+credit|tokenized\s+carbon|environmental\s+asset)\b", re.I)]),
    (RWACategory.COLLECTIBLES_ART.value, [re.compile(r"\b(collectible|tokenized\s+art|fine\s+art\s+token)\b", re.I)]),
    (RWACategory.INSURANCE_LINKED.value, [re.compile(r"\b(insurance[\s-]?linked|catastrophe\s+bond)\b", re.I)]),
    (RWACategory.TOKENIZATION_PLATFORMS.value, [re.compile(r"\b(tokenization\s+platform|securitize|polymath)\b", re.I)]),
    (RWACategory.CUSTODY_SETTLEMENT.value, [re.compile(r"\b(custody|settlement\s+infrastructure|dtcc)\b", re.I)]),
    (RWACategory.COMPLIANCE_IDENTITY.value, [re.compile(r"\b(kyc|kyb|compliance\s+infrastructure|identity\s+rail)\b", re.I)]),
    (RWACategory.RWA_INFRASTRUCTURE.value, [re.compile(r"\b(rwa\s+infrastructure|rwa\s+oracle|rwa\s+rail)\b", re.I)]),
]

_EVENT_TYPE_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (RWAEventType.FUNDING.value, [re.compile(r"\b(funding|raises?|series\s+[a-d]|seed\s+round)\b", re.I)]),
    (RWAEventType.REGULATORY.value, [re.compile(r"\b(regulat(?:ory|ion)|sec\b|license|approval|compliance\s+filing)\b", re.I)]),
    (RWAEventType.INSTITUTIONAL_ADOPTION.value, [re.compile(r"\b(institutional|blackrock|fidelity|franklin|adoption\s+by)\b", re.I)]),
    (RWAEventType.CUSTODY.value, [re.compile(r"\b(custod(?:y|ian)|safekeeping)\b", re.I)]),
    (RWAEventType.SETTLEMENT.value, [re.compile(r"\b(settlement|atomic\s+settle|t\+0)\b", re.I)]),
    (RWAEventType.COLLATERAL.value, [re.compile(r"\b(collateral|over[\s-]?collateral)\b", re.I)]),
    (RWAEventType.REDEMPTION.value, [re.compile(r"\b(redemption|redeem(?:able)?)\b", re.I)]),
    (RWAEventType.TOKEN_LAUNCH.value, [re.compile(r"\b(token\s+launch|tge|token\s+generation)\b", re.I)]),
    (RWAEventType.CHAIN_LAUNCH.value, [re.compile(r"\b(chain\s+launch|deploys?\s+on|goes\s+live\s+on)\b", re.I)]),
    (RWAEventType.ASSET_LAUNCH.value, [re.compile(r"\b(asset\s+launch|product\s+launch|launches?\s+(?:a|an|the)\s+tokenized)\b", re.I)]),
    (RWAEventType.PARTNERSHIP.value, [re.compile(r"\b(partnership|partners\s+with|collaborat)\b", re.I)]),
    (RWAEventType.INTEGRATION.value, [re.compile(r"\b(integrat(?:es|ion)|lists?\s+on|connects?\s+to)\b", re.I)]),
    (RWAEventType.ACQUISITION.value, [re.compile(r"\b(acqui(?:res|sition)|merges?\s+with)\b", re.I)]),
    (RWAEventType.MAINNET.value, [re.compile(r"\b(mainnet)\b", re.I)]),
    (RWAEventType.TESTNET.value, [re.compile(r"\b(testnet)\b", re.I)]),
    (RWAEventType.NEW_PROJECT.value, [re.compile(r"\b(new\s+(?:rwa|tokenization)\s+project|introduc(?:e|ing)|launches?\s+protocol)\b", re.I)]),
]


@dataclass
class RWAClassification:
    is_rwa: bool = False
    rwa_category: str = ""
    rwa_event_type: str = RWAEventType.OTHER.value
    signals: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.signals is None:
            self.signals = []


class RWAClassificationService:
    """Detect RWA membership, sub-category, and event type from text / meta."""

    def classify(self, doc: RawDocument) -> RWAClassification:
        meta = doc.meta or {}
        hint_cat = str(meta.get("rwa_category") or meta.get("subcategory") or "").strip().lower()
        hint_evt = str(meta.get("rwa_event_type") or "").strip().upper()
        blob = f"{doc.title}\n{doc.body}"

        is_rwa = bool(meta.get("is_rwa")) or self.is_rwa_text(blob)
        category = hint_cat if is_known_rwa_category(hint_cat) else self.detect_category(blob)
        event_type = hint_evt if hint_evt else self.detect_event_type(blob)
        if not event_type:
            event_type = RWAEventType.OTHER.value

        signals: list[str] = []
        if is_rwa:
            signals.append("rwa_membership")
        if category:
            signals.append(f"category:{category}")
        if event_type and event_type != RWAEventType.OTHER.value:
            signals.append(f"event:{event_type}")

        # If meta forced category or strong category match, treat as RWA
        if category and not is_rwa:
            is_rwa = True
            signals.append("rwa_via_category")

        return RWAClassification(
            is_rwa=is_rwa,
            rwa_category=category,
            rwa_event_type=event_type,
            signals=signals,
        )

    def is_rwa_text(self, text: str) -> bool:
        for pat in _RWA_MEMBERSHIP:
            if pat.search(text or ""):
                return True
        return False

    def detect_category(self, text: str) -> str:
        for cat, patterns in _CATEGORY_RULES:
            for pat in patterns:
                if pat.search(text or ""):
                    return cat
        return ""

    def detect_event_type(self, text: str) -> str:
        for evt, patterns in _EVENT_TYPE_RULES:
            for pat in patterns:
                if pat.search(text or ""):
                    return evt
        return RWAEventType.OTHER.value
