"""RWA taxonomy — extensible categories, event types, risk disclosures.

New categories / event types can be registered without schema rewrites:
they are stored as TEXT with validation against the known registry + allow-any
extension via `register_*` helpers and `is_known_*` checks.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class RWACategory(str, Enum):
    """First-class RWA sub-categories (extensible via register_category)."""

    TOKENIZED_TREASURIES = "tokenized_treasuries"
    REAL_ESTATE = "real_estate"
    PRIVATE_CREDIT = "private_credit"
    CORPORATE_CREDIT = "corporate_credit"
    CONSUMER_CREDIT = "consumer_credit"
    COMMODITIES = "commodities"
    GOLD_PRECIOUS_METALS = "gold_precious_metals"
    AGRICULTURE = "agriculture"
    TRADE_FINANCE = "trade_finance"
    INFRASTRUCTURE = "infrastructure"
    ENERGY = "energy"
    FUNDS = "funds"
    SECURITIES = "securities"
    BONDS = "bonds"
    STABLECOINS = "stablecoins"
    CARBON_ENVIRONMENTAL = "carbon_environmental"
    COLLECTIBLES_ART = "collectibles_art"
    INSURANCE_LINKED = "insurance_linked"
    RWA_INFRASTRUCTURE = "rwa_infrastructure"
    TOKENIZATION_PLATFORMS = "tokenization_platforms"
    CUSTODY_SETTLEMENT = "custody_settlement_infrastructure"
    COMPLIANCE_IDENTITY = "compliance_identity_infrastructure"


# Human labels for UI
RWA_CATEGORY_LABELS: dict[str, str] = {
    RWACategory.TOKENIZED_TREASURIES.value: "Tokenized Treasuries",
    RWACategory.REAL_ESTATE.value: "Real Estate",
    RWACategory.PRIVATE_CREDIT.value: "Private Credit",
    RWACategory.CORPORATE_CREDIT.value: "Corporate Credit",
    RWACategory.CONSUMER_CREDIT.value: "Consumer Credit",
    RWACategory.COMMODITIES.value: "Commodities",
    RWACategory.GOLD_PRECIOUS_METALS.value: "Gold/Precious Metals",
    RWACategory.AGRICULTURE.value: "Agriculture",
    RWACategory.TRADE_FINANCE.value: "Trade Finance",
    RWACategory.INFRASTRUCTURE.value: "Infrastructure",
    RWACategory.ENERGY.value: "Energy",
    RWACategory.FUNDS.value: "Funds",
    RWACategory.SECURITIES.value: "Securities",
    RWACategory.BONDS.value: "Bonds",
    RWACategory.STABLECOINS.value: "Stablecoins",
    RWACategory.CARBON_ENVIRONMENTAL.value: "Carbon/Environmental",
    RWACategory.COLLECTIBLES_ART.value: "Collectibles/Art",
    RWACategory.INSURANCE_LINKED.value: "Insurance-linked",
    RWACategory.RWA_INFRASTRUCTURE.value: "RWA Infrastructure",
    RWACategory.TOKENIZATION_PLATFORMS.value: "Tokenization Platforms",
    RWACategory.CUSTODY_SETTLEMENT.value: "Custody/Settlement Infrastructure",
    RWACategory.COMPLIANCE_IDENTITY.value: "Compliance/Identity Infrastructure",
}

# Mutable extension registry (no schema rewrite)
_EXTRA_CATEGORIES: dict[str, str] = {}


def register_category(key: str, label: str) -> None:
    k = (key or "").strip().lower().replace(" ", "_")
    if not k:
        raise ValueError("category key required")
    _EXTRA_CATEGORIES[k] = label or k.replace("_", " ").title()


def all_rwa_categories() -> dict[str, str]:
    out = dict(RWA_CATEGORY_LABELS)
    out.update(_EXTRA_CATEGORIES)
    return out


def is_known_rwa_category(key: str) -> bool:
    k = (key or "").strip().lower()
    return k in all_rwa_categories()


def category_label(key: str) -> str:
    cats = all_rwa_categories()
    k = (key or "").strip().lower()
    return cats.get(k, key or "Unknown")


class RWAEventType(str, Enum):
    NEW_PROJECT = "NEW_PROJECT"
    ASSET_LAUNCH = "ASSET_LAUNCH"
    FUNDING = "FUNDING"
    PARTNERSHIP = "PARTNERSHIP"
    TOKEN_LAUNCH = "TOKEN_LAUNCH"
    CHAIN_LAUNCH = "CHAIN_LAUNCH"
    INSTITUTIONAL_ADOPTION = "INSTITUTIONAL_ADOPTION"
    REGULATORY = "REGULATORY"
    CUSTODY = "CUSTODY"
    SETTLEMENT = "SETTLEMENT"
    COLLATERAL = "COLLATERAL"
    REDEMPTION = "REDEMPTION"
    INTEGRATION = "INTEGRATION"
    ACQUISITION = "ACQUISITION"
    MAINNET = "MAINNET"
    TESTNET = "TESTNET"
    OTHER = "OTHER"


_EXTRA_EVENT_TYPES: set[str] = set()


def register_event_type(key: str) -> None:
    k = (key or "").strip().upper()
    if not k:
        raise ValueError("event type required")
    _EXTRA_EVENT_TYPES.add(k)


def all_rwa_event_types() -> list[str]:
    base = [e.value for e in RWAEventType]
    extra = sorted(_EXTRA_EVENT_TYPES - set(base))
    return base + extra


def is_known_rwa_event_type(key: str) -> bool:
    k = (key or "").strip().upper()
    return k in set(all_rwa_event_types())


class AssetValueType(str, Enum):
    """Never label calculated_estimate as TVL."""

    VERIFIED_REPORTED = "verified_reported_value"
    CALCULATED_ESTIMATE = "calculated_estimate"
    UNAVAILABLE = "unavailable"


ASSET_VALUE_TYPE_LABELS = {
    AssetValueType.VERIFIED_REPORTED.value: "Verified reported value",
    AssetValueType.CALCULATED_ESTIMATE.value: "Calculated estimate (not TVL)",
    AssetValueType.UNAVAILABLE.value: "Unavailable",
}


class VerificationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REVIEW = "REVIEW"
    VERIFIED = "VERIFIED"
    TRACKING = "TRACKING"
    ARCHIVED = "ARCHIVED"


class ProvenanceTier(str, Enum):
    """Claim provenance trust ladder (RWA-specific labelling)."""

    OFFICIAL_ISSUER = "official_issuer"
    DOCS = "docs"
    REGULATORY_INSTITUTIONAL = "regulatory_institutional"
    ESTABLISHED_PUBLICATION = "established_publication"
    SECONDARY = "secondary"
    SOCIAL = "social"


PROVENANCE_TIER_LABELS = {
    ProvenanceTier.OFFICIAL_ISSUER.value: "Official issuer",
    ProvenanceTier.DOCS.value: "Docs",
    ProvenanceTier.REGULATORY_INSTITUTIONAL.value: "Regulatory/institutional",
    ProvenanceTier.ESTABLISHED_PUBLICATION.value: "Established publication",
    ProvenanceTier.SECONDARY.value: "Secondary",
    ProvenanceTier.SOCIAL.value: "Social",
}

# Map provenance → SourceTier-ish int (1 best … 6 worst) for scoring
PROVENANCE_TO_SOURCE_TIER = {
    ProvenanceTier.OFFICIAL_ISSUER.value: 1,
    ProvenanceTier.DOCS.value: 1,
    ProvenanceTier.REGULATORY_INSTITUTIONAL.value: 2,
    ProvenanceTier.ESTABLISHED_PUBLICATION.value: 2,
    ProvenanceTier.SECONDARY.value: 3,
    ProvenanceTier.SOCIAL.value: 4,
}


class DisclosureStatus(str, Enum):
    """Risk framework — disclosure indicators only (NOT buy/sell ratings)."""

    DISCLOSED = "DISCLOSED"
    NOT_DISCLOSED = "NOT DISCLOSED"
    UNKNOWN = "UNKNOWN"


DISCLOSURE_FIELDS = (
    "issuer_identity",
    "jurisdiction",
    "regulatory_status",
    "custody_arrangement",
    "collateral_description",
    "redemption_mechanism",
    "settlement_process",
    "audit_attestation",
    "tokenized_asset_value",
    "underlying_yield",
)


TOP_LEVEL_CATEGORY = "RWA — REAL-WORLD ASSETS"
TOP_LEVEL_SLUG = "rwa"

# Intelligence Center / UI section keys
RWA_UI_SECTIONS = (
    ("Breaking", "breaking"),
    ("New Projects", "new_projects"),
    ("Tokenized Treasuries", RWACategory.TOKENIZED_TREASURIES.value),
    ("Real Estate", RWACategory.REAL_ESTATE.value),
    ("Private Credit", RWACategory.PRIVATE_CREDIT.value),
    ("Commodities", RWACategory.COMMODITIES.value),
    ("Agriculture", RWACategory.AGRICULTURE.value),
    ("Infrastructure", RWACategory.INFRASTRUCTURE.value),
    ("Funding", "funding"),
    ("Institutional Adoption", "institutional_adoption"),
    ("Regulatory", "regulatory"),
    ("Trends", "trends"),
)

RWA_DISCLAIMER = (
    "RWA Intelligence is educational / disclosure-based research only — "
    "not financial advice. Indicators are DISCLOSED / NOT DISCLOSED / UNKNOWN. "
    "Never treat DEMO / SYNTHETIC rows as live market data, verified TVL, or "
    "investment recommendations. MCCC does not execute trades or custody assets."
)


def narrative_slugs_from_categories(categories: Iterable[str]) -> list[str]:
    """Build narrative slug candidates from observed RWA categories only."""
    out = []
    for c in categories:
        k = (c or "").strip().lower()
        if k and is_known_rwa_category(k):
            out.append(f"rwa-{k.replace('_', '-')}")
    return out
