"""Source registry — tiers, adapters, rate-limit metadata. No aggressive scraping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from mccc.intelligence.schema import SourceTier


# Robots / ToS stance (documented for operators)
ROBOTS_TOS_STANCE = (
    "MCCC Intelligence prefers official public RSS / Atom feeds and documented APIs. "
    "We do not aggressively scrape HTML, bypass paywalls, ignore robots.txt, or hammer endpoints. "
    "Adapters must respect rate limits (min interval) and fail soft. "
    "DEMO seed data is used when live fetch is unavailable."
)


@dataclass
class SourceDefinition:
    key: str
    name: str
    tier: SourceTier
    source_type: str  # rss | official | demo | stub
    feed_url: str = ""
    homepage: str = ""
    enabled: bool = True
    min_interval_seconds: int = 900
    notes: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


# Curated public / official-ish feeds — fetch may fail offline; adapters soft-fail.
DEFAULT_SOURCES: list[SourceDefinition] = [
    SourceDefinition(
        key="demo_seed",
        name="MCCC DEMO Seed",
        tier=SourceTier.UNVERIFIED,
        source_type="demo",
        enabled=True,
        min_interval_seconds=0,
        notes="Clearly labelled DEMO / SAMPLE events for offline UI.",
    ),
    SourceDefinition(
        key="cointelegraph_rss",
        name="CoinTelegraph RSS",
        tier=SourceTier.MAJOR_NEWS,
        source_type="rss",
        feed_url="https://cointelegraph.com/rss",
        homepage="https://cointelegraph.com/",
        min_interval_seconds=1800,
        notes="Public RSS; respect publisher ToS / rate limits.",
    ),
    SourceDefinition(
        key="coindesk_rss",
        name="CoinDesk RSS",
        tier=SourceTier.MAJOR_NEWS,
        source_type="rss",
        feed_url="https://www.coindesk.com/arc/outboundfeeds/rss/",
        homepage="https://www.coindesk.com/",
        min_interval_seconds=1800,
        notes="Public RSS when reachable; soft-fail offline.",
    ),
    SourceDefinition(
        key="ethereum_blog_rss",
        name="Ethereum Foundation Blog",
        tier=SourceTier.OFFICIAL,
        source_type="rss",
        feed_url="https://blog.ethereum.org/en/feed.xml",
        homepage="https://blog.ethereum.org/",
        min_interval_seconds=3600,
        notes="Official public feed — Tier 1.",
    ),
]


class SourceService:
    """Manage intelligence sources and tier lookups."""

    def __init__(self, sources: Optional[list[SourceDefinition]] = None) -> None:
        self._sources = {s.key: s for s in (sources or list(DEFAULT_SOURCES))}

    def list_sources(self, enabled_only: bool = False) -> list[SourceDefinition]:
        items = list(self._sources.values())
        if enabled_only:
            items = [s for s in items if s.enabled]
        return sorted(items, key=lambda s: (int(s.tier), s.name))

    def get(self, key: str) -> Optional[SourceDefinition]:
        return self._sources.get(key)

    def register(self, source: SourceDefinition) -> None:
        self._sources[source.key] = source

    def tier_for(self, key: str) -> SourceTier:
        src = self._sources.get(key)
        return src.tier if src else SourceTier.UNVERIFIED

    def robots_stance(self) -> str:
        return ROBOTS_TOS_STANCE
