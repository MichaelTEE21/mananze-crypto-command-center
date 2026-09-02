"""DEMO / SYNTHETIC seed fixtures — clearly labelled; never baked into UI widgets.

These are offline fixtures for the Intelligence Center when live RSS is unavailable.
Every record sets is_demo=True and uses DEMO/SAMPLE wording. Amounts/investors/TGEs
that are unknown stay "Not disclosed" / "Unknown" / "Unconfirmed".
"""
from __future__ import annotations

from mccc.intelligence.schema import (
    NOT_DISCLOSED,
    UNKNOWN,
    UNCONFIRMED_LABEL,
    RawDocument,
    utc_now_iso,
)

_NOW = None  # filled lazily so timestamps refresh on import if needed


def _ts() -> str:
    return utc_now_iso()


# Fixture raw docs — source_url uses example.com placeholders (not fake news sites).
DEMO_RAW_DOCUMENTS: list[RawDocument] = [
    RawDocument(
        title="[DEMO] Sample L2 mainnet upgrade window announced by foundation blog",
        body=(
            "DEMO / SYNTHETIC: A fictional Layer-2 foundation blog notes an upcoming "
            "protocol upgrade window. No mainnet date is confirmed in this sample. "
            f"TGE: {UNKNOWN}. Funding: {NOT_DISCLOSED}."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/l2-upgrade-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-08-28T10:00:00+00:00",
        is_demo=True,
        meta={"category_hint": "technology", "project": "DEMO-L2", "tags": ["demo", "l2", "upgrade"]},
    ),
    RawDocument(
        title="[DEMO] New open-source DeFi toolkit repository surfaced",
        body=(
            "DEMO / SYNTHETIC: A sample discovery of a new open-source toolkit. "
            f"Investors: {NOT_DISCLOSED}. Token: {UNKNOWN}. Status: research signal only."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/defi-toolkit-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-08-29T14:30:00+00:00",
        is_demo=True,
        meta={"category_hint": "new_projects", "project": "DEMO-Toolkit", "tags": ["demo", "defi", "oss"]},
    ),
    RawDocument(
        title="[DEMO] Series sample funding mention — amount not disclosed",
        body=(
            "DEMO / SYNTHETIC: Sample funding signal text. "
            f"Round size: {NOT_DISCLOSED}. Lead investor: {UNCONFIRMED_LABEL}. "
            "Do not treat as a real raise."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/funding-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-08-30T09:15:00+00:00",
        is_demo=True,
        meta={
            "category_hint": "funding",
            "project": "DEMO-Protocol",
            "tags": ["demo", "funding"],
            "funding_amount": NOT_DISCLOSED,
        },
    ),
    RawDocument(
        title="[DEMO] Possible points campaign — eligibility unconfirmed",
        body=(
            "DEMO / SYNTHETIC: Sample airdrop-style signal. "
            f"Eligibility: {UNCONFIRMED_LABEL}. Claim page: none in sample. "
            "Never presents as a confirmed airdrop."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/airdrop-signal-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-08-31T16:00:00+00:00",
        is_demo=True,
        meta={
            "category_hint": "airdrop_signals",
            "project": "DEMO-Points",
            "tags": ["demo", "points", "airdrop"],
            "airdrop_signal_status": "UNCONFIRMED",
        },
    ),
    RawDocument(
        title="[DEMO] Token unlock calendar entry — schedule unknown",
        body=(
            "DEMO / SYNTHETIC: Placeholder token-event card. "
            f"Unlock schedule: {UNKNOWN}. Price impact: not estimated."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/token-event-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-09-01T08:00:00+00:00",
        is_demo=True,
        meta={"category_hint": "token_events", "project": "DEMO-Token", "token": "DEMO", "tags": ["demo", "unlock"]},
    ),
    RawDocument(
        title="[DEMO] Breaking: sample network congestion advisory",
        body=(
            "DEMO / SYNTHETIC: Illustrative breaking-style advisory for UI layout. "
            "Not a live outage. Always verify against official status pages."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/breaking-congestion-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-09-01T20:45:00+00:00",
        is_demo=True,
        meta={"category_hint": "breaking", "project": "DEMO-Chain", "tags": ["demo", "network"]},
    ),
    RawDocument(
        title="[DEMO] Narrative watch: modular data-availability discussion",
        body=(
            "DEMO / SYNTHETIC: Sample narrative cluster label for Trending Narratives UI. "
            f"No partnership claims. Status: {UNCONFIRMED_LABEL}."
        ),
        source_name="MCCC DEMO Seed",
        source_url="https://example.com/demo/narrative-da-sample",
        source_type="demo",
        source_tier=5,
        published_at="2026-09-01T12:00:00+00:00",
        is_demo=True,
        meta={"category_hint": "narratives", "project": UNKNOWN, "tags": ["demo", "da", "modular"]},
    ),
]


DEMO_NARRATIVES = [
    {
        "slug": "demo-modular-da",
        "title": "[DEMO] Modular data availability",
        "summary": "DEMO / SYNTHETIC narrative cluster — research framing only.",
        "is_demo": True,
        "tags": ["demo", "da", "modular"],
    },
    {
        "slug": "demo-restaking",
        "title": "[DEMO] Restaking diligence theme",
        "summary": "DEMO / SYNTHETIC — no yield claims; Unknown APY.",
        "is_demo": True,
        "tags": ["demo", "restaking"],
    },
]
