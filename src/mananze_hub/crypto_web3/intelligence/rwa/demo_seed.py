"""DEMO / SYNTHETIC RWA seed fixtures — clearly labelled; replaceable by live later.

Uses example.com placeholders only. Never invents real funding, TVL, investors,
regulatory approvals, or TGE dates. Missing fields stay Unknown / Not disclosed.
"""
from __future__ import annotations

from uuid import uuid4

from mccc.intelligence.rwa.schema import (
    ClaimProvenance,
    RiskDisclosure,
    RWAProfile,
    TokenizedAssetValue,
)
from mccc.intelligence.rwa.taxonomy import (
    AssetValueType,
    DisclosureStatus,
    ProvenanceTier,
    RWACategory,
    VerificationStatus,
)
from mccc.intelligence.schema import (
    NOT_DISCLOSED,
    UNKNOWN,
    UNCONFIRMED_LABEL,
    RawDocument,
    utc_now_iso,
)


def _disc(key: str, status: str, detail: str = "") -> RiskDisclosure:
    return RiskDisclosure(field_key=key, status=status, detail=detail)


def _prov(**kwargs) -> ClaimProvenance:
    return ClaimProvenance(**kwargs)


def build_demo_profiles() -> list[RWAProfile]:
    """Small DEMO set spanning major RWA UI sections."""
    now = utc_now_iso()
    stale_ts = "2025-01-15T12:00:00+00:00"

    profiles: list[RWAProfile] = []

    p1 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Treasury Rail Sample",
        ticker="DEMO-UST",
        description=(
            "DEMO / SYNTHETIC: Illustrative tokenized-treasury research card. "
            f"Issuer identity educational only. Yield: {UNKNOWN}."
        ),
        rwa_category=RWACategory.TOKENIZED_TREASURIES.value,
        asset_type="U.S. Treasury exposure (sample)",
        blockchain="ethereum",
        website_url="https://example.com/demo/rwa-treasury",
        docs_url="https://example.com/demo/rwa-treasury/docs",
        launch_status="DEMO sample",
        token_status=UNKNOWN,
        tokenization_model="DEMO permissioned mint (sample)",
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        custody_info=NOT_DISCLOSED,
        issuer_info=NOT_DISCLOSED,
        collateral_info=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "treasuries"],
    )
    p1.set_asset_value(
        TokenizedAssetValue(
            value_type=AssetValueType.UNAVAILABLE.value,
            amount=UNKNOWN,
            currency="USD",
            measured_at="",
            source="DEMO seed",
            source_url="https://example.com/demo/rwa-treasury",
            notes="No verified reported value in DEMO seed — not TVL.",
        )
    )
    p1.disclosures = [
        _disc("issuer_identity", DisclosureStatus.NOT_DISCLOSED.value),
        _disc("jurisdiction", DisclosureStatus.UNKNOWN.value),
        _disc("regulatory_status", DisclosureStatus.NOT_DISCLOSED.value),
        _disc("custody_arrangement", DisclosureStatus.NOT_DISCLOSED.value),
        _disc("redemption_mechanism", DisclosureStatus.UNKNOWN.value),
        _disc("tokenized_asset_value", DisclosureStatus.NOT_DISCLOSED.value),
    ]
    p1.provenance = [
        _prov(
            source="MCCC DEMO Seed",
            source_url="https://example.com/demo/rwa-treasury",
            source_type="demo",
            published_at="2026-08-20T10:00:00+00:00",
            discovered_at=now,
            confidence="UNCONFIRMED",
            provenance_tier=ProvenanceTier.SECONDARY.value,
            claim_key="existence",
            claim_value="DEMO sample profile only",
        )
    ]
    profiles.append(p1)

    p2 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Property Token Sample",
        ticker="DEMO-RE",
        description=(
            "DEMO / SYNTHETIC: Sample real-estate tokenization research card. "
            f"Property value: {NOT_DISCLOSED}. Not an offering."
        ),
        rwa_category=RWACategory.REAL_ESTATE.value,
        asset_type="Fractional property interest (sample)",
        blockchain="polygon",
        website_url="https://example.com/demo/rwa-real-estate",
        docs_url="https://example.com/demo/rwa-real-estate/docs",
        launch_status=UNKNOWN,
        token_status=UNKNOWN,
        tokenization_model=UNKNOWN,
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        custody_info=NOT_DISCLOSED,
        issuer_info=NOT_DISCLOSED,
        collateral_info=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "real_estate"],
    )
    p2.set_asset_value(TokenizedAssetValue.unavailable())
    p2.disclosures = [
        _disc("issuer_identity", DisclosureStatus.NOT_DISCLOSED.value),
        _disc("collateral_description", DisclosureStatus.NOT_DISCLOSED.value),
        _disc("regulatory_status", DisclosureStatus.NOT_DISCLOSED.value),
    ]
    profiles.append(p2)

    p3 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Private Credit Pool Sample",
        ticker="DEMO-PC",
        description=(
            "DEMO / SYNTHETIC: Private-credit style research card. "
            "Shows a calculated estimate labelled honestly (not TVL) with a stale measurement timestamp."
        ),
        rwa_category=RWACategory.PRIVATE_CREDIT.value,
        asset_type="Private credit pool (sample)",
        blockchain="ethereum",
        website_url="https://example.com/demo/rwa-private-credit",
        docs_url="",
        launch_status="DEMO sample",
        token_status=UNKNOWN,
        tokenization_model=UNKNOWN,
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        custody_info=NOT_DISCLOSED,
        issuer_info=NOT_DISCLOSED,
        collateral_info=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.REVIEW.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "private_credit"],
    )
    p3.set_asset_value(
        TokenizedAssetValue(
            value_type=AssetValueType.CALCULATED_ESTIMATE.value,
            amount="Not disclosed as verified",
            currency="USD",
            measured_at=stale_ts,
            source="DEMO seed calculator placeholder",
            source_url="https://example.com/demo/rwa-private-credit",
            notes="Calculated estimate only — NEVER call this TVL. Timestamp intentionally stale.",
        )
    )
    p3.disclosures = [
        _disc("tokenized_asset_value", DisclosureStatus.NOT_DISCLOSED.value, "Estimate only"),
        _disc("underlying_yield", DisclosureStatus.UNKNOWN.value),
        _disc("custody_arrangement", DisclosureStatus.NOT_DISCLOSED.value),
    ]
    profiles.append(p3)

    p4 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Gold Vault Sample",
        ticker="DEMO-AU",
        description=(
            "DEMO / SYNTHETIC: Precious-metals research card. "
            f"Vault attestation: {UNCONFIRMED_LABEL}."
        ),
        rwa_category=RWACategory.GOLD_PRECIOUS_METALS.value,
        asset_type="Allocated gold claim (sample)",
        blockchain="ethereum",
        website_url="https://example.com/demo/rwa-gold",
        docs_url="https://example.com/demo/rwa-gold/docs",
        launch_status=UNKNOWN,
        token_status=UNKNOWN,
        tokenization_model=UNKNOWN,
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        custody_info=NOT_DISCLOSED,
        issuer_info=NOT_DISCLOSED,
        collateral_info=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "gold"],
    )
    p4.set_asset_value(TokenizedAssetValue.unavailable())
    profiles.append(p4)

    p5 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Agri Finance Sample",
        ticker=UNKNOWN,
        description="DEMO / SYNTHETIC: Agriculture / agri-finance research placeholder.",
        rwa_category=RWACategory.AGRICULTURE.value,
        asset_type="Agri receivable (sample)",
        blockchain=UNKNOWN,
        website_url="https://example.com/demo/rwa-agriculture",
        launch_status=UNKNOWN,
        token_status=UNKNOWN,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "agriculture"],
    )
    p5.set_asset_value(TokenizedAssetValue.unavailable())
    profiles.append(p5)

    p6 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Tokenization Platform Sample",
        ticker="DEMO-TP",
        description=(
            "DEMO / SYNTHETIC: Tokenization-platform / RWA infrastructure research card. "
            f"Partnerships: {UNCONFIRMED_LABEL}."
        ),
        rwa_category=RWACategory.TOKENIZATION_PLATFORMS.value,
        asset_type="Platform (sample)",
        blockchain="multi",
        website_url="https://example.com/demo/rwa-platform",
        docs_url="https://example.com/demo/rwa-platform/docs",
        launch_status="DEMO sample",
        token_status=UNKNOWN,
        tokenization_model="Platform rails (sample)",
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        custody_info=NOT_DISCLOSED,
        issuer_info=NOT_DISCLOSED,
        collateral_info=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "infrastructure", "platform"],
    )
    p6.set_asset_value(TokenizedAssetValue.unavailable())
    profiles.append(p6)

    p7 = RWAProfile(
        id=str(uuid4()),
        project_name="DEMO Custody Settlement Sample",
        ticker=UNKNOWN,
        description="DEMO / SYNTHETIC: Custody/settlement infrastructure research placeholder.",
        rwa_category=RWACategory.CUSTODY_SETTLEMENT.value,
        asset_type="Infrastructure (sample)",
        blockchain="ethereum",
        website_url="https://example.com/demo/rwa-custody",
        launch_status=UNKNOWN,
        token_status=UNKNOWN,
        funding_notes=NOT_DISCLOSED,
        confidence="UNCONFIRMED",
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=True,
        tags=["demo", "synthetic", "rwa", "custody"],
    )
    p7.set_asset_value(TokenizedAssetValue.unavailable())
    profiles.append(p7)

    return profiles


def build_demo_raw_documents() -> list[RawDocument]:
    """Raw docs for intelligence pipeline — RWA category_hint + is_rwa."""
    return [
        RawDocument(
            title="[DEMO] Sample tokenized treasury product note — amount not disclosed",
            body=(
                "DEMO / SYNTHETIC: Illustrative RWA treasury signal. "
                f"Tokenized asset value: {UNKNOWN}. Regulatory approval: {NOT_DISCLOSED}. "
                "Do not treat as a live product launch."
            ),
            source_name="MCCC DEMO RWA Seed",
            source_url="https://example.com/demo/rwa-event-treasury",
            source_type="demo",
            source_tier=5,
            published_at="2026-08-25T11:00:00+00:00",
            is_demo=True,
            meta={
                "category_hint": "rwa",
                "is_rwa": True,
                "rwa_category": RWACategory.TOKENIZED_TREASURIES.value,
                "rwa_event_type": "ASSET_LAUNCH",
                "project": "DEMO Treasury Rail Sample",
                "tags": ["demo", "rwa", "treasuries"],
            },
        ),
        RawDocument(
            title="[DEMO] Sample private credit pool research note",
            body=(
                "DEMO / SYNTHETIC: Private credit RWA signal for UI. "
                f"Funding: {NOT_DISCLOSED}. Investors: {NOT_DISCLOSED}."
            ),
            source_name="MCCC DEMO RWA Seed",
            source_url="https://example.com/demo/rwa-event-credit",
            source_type="demo",
            source_tier=5,
            published_at="2026-08-27T09:00:00+00:00",
            is_demo=True,
            meta={
                "category_hint": "rwa",
                "is_rwa": True,
                "rwa_category": RWACategory.PRIVATE_CREDIT.value,
                "rwa_event_type": "NEW_PROJECT",
                "project": "DEMO Private Credit Pool Sample",
                "tags": ["demo", "rwa", "private_credit"],
            },
        ),
        RawDocument(
            title="[DEMO] Sample institutional RWA adoption discussion — unconfirmed",
            body=(
                "DEMO / SYNTHETIC: Institutional adoption narrative placeholder. "
                f"Named institutions in live sense: none. Status: {UNCONFIRMED_LABEL}."
            ),
            source_name="MCCC DEMO RWA Seed",
            source_url="https://example.com/demo/rwa-event-institutional",
            source_type="demo",
            source_tier=5,
            published_at="2026-08-30T15:00:00+00:00",
            is_demo=True,
            meta={
                "category_hint": "rwa",
                "is_rwa": True,
                "rwa_category": RWACategory.RWA_INFRASTRUCTURE.value,
                "rwa_event_type": "INSTITUTIONAL_ADOPTION",
                "project": UNKNOWN,
                "tags": ["demo", "rwa", "institutional"],
            },
        ),
        RawDocument(
            title="[DEMO] Sample RWA regulatory watch item — no approval claimed",
            body=(
                "DEMO / SYNTHETIC: Regulatory-themed RWA card. "
                f"Approval status: {NOT_DISCLOSED}. Never invents licenses."
            ),
            source_name="MCCC DEMO RWA Seed",
            source_url="https://example.com/demo/rwa-event-regulatory",
            source_type="demo",
            source_tier=5,
            published_at="2026-09-01T08:30:00+00:00",
            is_demo=True,
            meta={
                "category_hint": "rwa",
                "is_rwa": True,
                "rwa_category": RWACategory.COMPLIANCE_IDENTITY.value,
                "rwa_event_type": "REGULATORY",
                "project": "DEMO Custody Settlement Sample",
                "tags": ["demo", "rwa", "regulatory"],
            },
        ),
        RawDocument(
            title="[DEMO] Sample real estate tokenization research signal",
            body=(
                "DEMO / SYNTHETIC: Real estate RWA signal. "
                f"Asset appraisal: {NOT_DISCLOSED}. Offering: none."
            ),
            source_name="MCCC DEMO RWA Seed",
            source_url="https://example.com/demo/rwa-event-re",
            source_type="demo",
            source_tier=5,
            published_at="2026-08-22T13:00:00+00:00",
            is_demo=True,
            meta={
                "category_hint": "rwa",
                "is_rwa": True,
                "rwa_category": RWACategory.REAL_ESTATE.value,
                "rwa_event_type": "NEW_PROJECT",
                "project": "DEMO Property Token Sample",
                "tags": ["demo", "rwa", "real_estate"],
            },
        ),
    ]


DEMO_RWA_NARRATIVES = [
    {
        "slug": "rwa-tokenized-treasuries",
        "title": "[DEMO] RWA · Tokenized Treasuries",
        "summary": "DEMO / SYNTHETIC narrative cluster from seed profiles — research framing only.",
        "is_demo": True,
        "tags": ["demo", "rwa", "treasuries"],
    },
    {
        "slug": "rwa-private-credit",
        "title": "[DEMO] RWA · Private Credit",
        "summary": "DEMO / SYNTHETIC — no yield claims; Unknown APY.",
        "is_demo": True,
        "tags": ["demo", "rwa", "private_credit"],
    },
]
