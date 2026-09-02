"""RWA profile / asset-value / claim provenance dataclasses."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional
from uuid import uuid4

from mccc.intelligence.rwa.taxonomy import (
    AssetValueType,
    DisclosureStatus,
    VerificationStatus,
)
from mccc.intelligence.schema import (
    NOT_DISCLOSED,
    UNKNOWN,
    utc_now_iso,
)


@dataclass
class ClaimProvenance:
    """Provenance attached to important RWA claims."""

    source: str = ""
    source_url: str = ""
    source_type: str = ""
    published_at: str = ""
    discovered_at: str = ""
    confidence: str = "UNCONFIRMED"
    provenance_tier: str = "secondary"
    claim_key: str = ""
    claim_value: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ClaimProvenance":
        return cls(
            source=str(d.get("source") or ""),
            source_url=str(d.get("source_url") or ""),
            source_type=str(d.get("source_type") or ""),
            published_at=str(d.get("published_at") or ""),
            discovered_at=str(d.get("discovered_at") or ""),
            confidence=str(d.get("confidence") or "UNCONFIRMED"),
            provenance_tier=str(d.get("provenance_tier") or "secondary"),
            claim_key=str(d.get("claim_key") or ""),
            claim_value=str(d.get("claim_value") or ""),
        )


@dataclass
class TokenizedAssetValue:
    """Asset value with measurement timestamp — never call estimates TVL."""

    value_type: str = AssetValueType.UNAVAILABLE.value
    amount: str = UNKNOWN
    currency: str = "USD"
    measured_at: str = ""
    source: str = ""
    source_url: str = ""
    notes: str = ""
    is_stale: bool = False

    def display_label(self) -> str:
        if self.value_type == AssetValueType.CALCULATED_ESTIMATE.value:
            return "Calculated estimate (not TVL)"
        if self.value_type == AssetValueType.VERIFIED_REPORTED.value:
            return "Verified reported value"
        return "Unavailable"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["display_label"] = self.display_label()
        return d

    @classmethod
    def unavailable(cls) -> "TokenizedAssetValue":
        return cls(
            value_type=AssetValueType.UNAVAILABLE.value,
            amount=UNKNOWN,
            notes="No tokenized asset value disclosed.",
        )

    @classmethod
    def from_dict(cls, d: Optional[dict[str, Any]]) -> "TokenizedAssetValue":
        if not d:
            return cls.unavailable()
        return cls(
            value_type=str(d.get("value_type") or AssetValueType.UNAVAILABLE.value),
            amount=str(d.get("amount") or UNKNOWN),
            currency=str(d.get("currency") or "USD"),
            measured_at=str(d.get("measured_at") or ""),
            source=str(d.get("source") or ""),
            source_url=str(d.get("source_url") or ""),
            notes=str(d.get("notes") or ""),
            is_stale=bool(d.get("is_stale")),
        )


@dataclass
class RiskDisclosure:
    """Disclosure-only risk framework — not buy/sell ratings."""

    field_key: str
    status: str = DisclosureStatus.UNKNOWN.value
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RWAProfile:
    """RWA project directory profile — links to projects / intelligence events."""

    id: str
    project_name: str
    ticker: str = UNKNOWN
    description: str = ""
    rwa_category: str = ""
    asset_type: str = UNKNOWN
    blockchain: str = UNKNOWN
    website_url: str = ""
    docs_url: str = ""
    launch_status: str = UNKNOWN
    token_status: str = UNKNOWN
    tokenization_model: str = UNKNOWN
    jurisdiction: str = UNKNOWN
    regulatory_status: str = NOT_DISCLOSED
    custody_info: str = NOT_DISCLOSED
    issuer_info: str = NOT_DISCLOSED
    collateral_info: str = NOT_DISCLOSED
    funding_notes: str = NOT_DISCLOSED
    funding_round_id: str = ""
    tokenized_asset_value_json: str = ""
    confidence: str = "UNCONFIRMED"
    verification_status: str = VerificationStatus.DISCOVERED.value
    discovered_at: str = ""
    last_checked_at: str = ""
    created_at: str = ""
    updated_at: str = ""
    project_id: Optional[int] = None
    source_event_id: str = ""
    is_demo: bool = False
    tags: list[str] = field(default_factory=list)
    disclosures: list[RiskDisclosure] = field(default_factory=list)
    provenance: list[ClaimProvenance] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.discovered_at:
            self.discovered_at = now
        if not self.last_checked_at:
            self.last_checked_at = now
        if self.is_demo and "demo" not in [t.lower() for t in self.tags]:
            self.tags = ["demo", "synthetic"] + list(self.tags)

    def asset_value(self) -> TokenizedAssetValue:
        if not self.tokenized_asset_value_json:
            return TokenizedAssetValue.unavailable()
        try:
            raw = json.loads(self.tokenized_asset_value_json)
        except json.JSONDecodeError:
            return TokenizedAssetValue.unavailable()
        return TokenizedAssetValue.from_dict(raw if isinstance(raw, dict) else {})

    def set_asset_value(self, value: TokenizedAssetValue) -> None:
        self.tokenized_asset_value_json = json.dumps(value.to_dict())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tags_json"] = json.dumps(self.tags)
        d["disclosures_json"] = json.dumps([x.to_dict() for x in self.disclosures])
        d["provenance_json"] = json.dumps([x.to_dict() for x in self.provenance])
        d["asset_value"] = self.asset_value().to_dict()
        d["display_name"] = (
            f"[DEMO] {self.project_name}" if self.is_demo and not str(self.project_name).upper().startswith("[DEMO]")
            and not str(self.project_name).upper().startswith("DEMO")
            else self.project_name
        )
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RWAProfile":
        tags = row.get("tags")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags or "[]")
            except json.JSONDecodeError:
                tags = []
        disclosures_raw = row.get("disclosures") or row.get("disclosures_json")
        if isinstance(disclosures_raw, str):
            try:
                disclosures_raw = json.loads(disclosures_raw or "[]")
            except json.JSONDecodeError:
                disclosures_raw = []
        disclosures: list[RiskDisclosure] = []
        if isinstance(disclosures_raw, list):
            for item in disclosures_raw:
                if isinstance(item, dict) and item.get("field_key"):
                    disclosures.append(
                        RiskDisclosure(
                            field_key=str(item["field_key"]),
                            status=str(item.get("status") or DisclosureStatus.UNKNOWN.value),
                            detail=str(item.get("detail") or ""),
                        )
                    )
        prov_raw = row.get("provenance") or row.get("provenance_json")
        if isinstance(prov_raw, str):
            try:
                prov_raw = json.loads(prov_raw or "[]")
            except json.JSONDecodeError:
                prov_raw = []
        provenance: list[ClaimProvenance] = []
        if isinstance(prov_raw, list):
            for item in prov_raw:
                if isinstance(item, dict):
                    provenance.append(ClaimProvenance.from_dict(item))
        pid = row.get("project_id")
        return cls(
            id=str(row.get("id") or uuid4()),
            project_name=row.get("project_name") or UNKNOWN,
            ticker=row.get("ticker") or UNKNOWN,
            description=row.get("description") or "",
            rwa_category=row.get("rwa_category") or "",
            asset_type=row.get("asset_type") or UNKNOWN,
            blockchain=row.get("blockchain") or UNKNOWN,
            website_url=row.get("website_url") or "",
            docs_url=row.get("docs_url") or "",
            launch_status=row.get("launch_status") or UNKNOWN,
            token_status=row.get("token_status") or UNKNOWN,
            tokenization_model=row.get("tokenization_model") or UNKNOWN,
            jurisdiction=row.get("jurisdiction") or UNKNOWN,
            regulatory_status=row.get("regulatory_status") or NOT_DISCLOSED,
            custody_info=row.get("custody_info") or NOT_DISCLOSED,
            issuer_info=row.get("issuer_info") or NOT_DISCLOSED,
            collateral_info=row.get("collateral_info") or NOT_DISCLOSED,
            funding_notes=row.get("funding_notes") or NOT_DISCLOSED,
            funding_round_id=row.get("funding_round_id") or "",
            tokenized_asset_value_json=row.get("tokenized_asset_value_json") or "",
            confidence=row.get("confidence") or "UNCONFIRMED",
            verification_status=row.get("verification_status")
            or VerificationStatus.DISCOVERED.value,
            discovered_at=row.get("discovered_at") or "",
            last_checked_at=row.get("last_checked_at") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
            project_id=int(pid) if pid is not None else None,
            source_event_id=row.get("source_event_id") or "",
            is_demo=bool(row.get("is_demo")),
            tags=list(tags or []),
            disclosures=disclosures,
            provenance=provenance,
        )
