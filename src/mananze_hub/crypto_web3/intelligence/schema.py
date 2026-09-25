"""Intelligence event schema, enums, and value helpers — Phase 1 foundation."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum, Enum
from typing import Any, Optional
from uuid import uuid4


class SourceTier(IntEnum):
    """1 = highest trust (official), 5 = lowest (unverified / DEMO)."""

    OFFICIAL = 1
    MAJOR_NEWS = 2
    AGGREGATOR = 3
    SOCIAL = 4
    UNVERIFIED = 5


class EventCategory(str, Enum):
    BREAKING = "breaking"
    NEW_PROJECTS = "new_projects"
    FUNDING = "funding"
    AIRDROP_SIGNALS = "airdrop_signals"
    TOKEN_EVENTS = "token_events"
    TECHNOLOGY = "technology"
    NARRATIVES = "narratives"
    RWA = "rwa"


class Confidence(str, Enum):
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCONFIRMED = "UNCONFIRMED"


class AirdropSignalStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    POSSIBLE = "POSSIBLE"
    UNCONFIRMED = "UNCONFIRMED"
    RUMOR = "RUMOR"


class CandidateProjectStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REVIEW = "REVIEW"
    VERIFIED = "VERIFIED"
    TRACKING = "TRACKING"


class ImportanceBand(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EventStatus(str, Enum):
    ACTIVE = "ACTIVE"
    IGNORED = "IGNORED"
    ARCHIVED = "ARCHIVED"
    DEMO = "DEMO"


CATEGORY_LABELS = {
    EventCategory.BREAKING.value: "Breaking",
    EventCategory.NEW_PROJECTS.value: "New Projects",
    EventCategory.FUNDING.value: "Funding",
    EventCategory.AIRDROP_SIGNALS.value: "Airdrop Signals",
    EventCategory.TOKEN_EVENTS.value: "Token Events",
    EventCategory.TECHNOLOGY.value: "Technology",
    EventCategory.NARRATIVES.value: "Narratives",
    EventCategory.RWA.value: "RWA — Real-World Assets",
}

UNKNOWN = "Unknown"
NOT_DISCLOSED = "Not disclosed"
UNCONFIRMED_LABEL = "Unconfirmed"

DISCLAIMER = (
    "Intelligence is informational / research signals only — not financial advice. "
    "Never treat DEMO / SAMPLE items as live market data or verified facts."
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def importance_band(score: int) -> ImportanceBand:
    s = max(0, min(100, int(score)))
    if s >= 80:
        return ImportanceBand.CRITICAL
    if s >= 60:
        return ImportanceBand.HIGH
    if s >= 40:
        return ImportanceBand.MEDIUM
    return ImportanceBand.LOW


def content_fingerprint(title: str, source_url: str = "", summary: str = "") -> str:
    """Stable hash for dedupe clustering (title + url + summary stem)."""
    norm_title = re.sub(r"\s+", " ", (title or "").strip().lower())
    norm_url = (source_url or "").strip().lower().rstrip("/")
    stem = re.sub(r"\s+", " ", (summary or "").strip().lower())[:240]
    raw = f"{norm_title}|{norm_url}|{stem}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def cluster_key(title: str, project: str = "", category: str = "") -> str:
    """Loose cluster key: normalized title tokens + project + category."""
    tokens = re.findall(r"[a-z0-9]+", (title or "").lower())
    stop = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "with"}
    keep = [t for t in tokens if t not in stop][:8]
    proj = re.sub(r"\s+", " ", (project or "").strip().lower())
    cat = (category or "").strip().lower()
    return hashlib.sha256(f"{' '.join(keep)}|{proj}|{cat}".encode()).hexdigest()[:24]


@dataclass
class RelatedSource:
    name: str
    url: str = ""
    tier: int = int(SourceTier.UNVERIFIED)
    published_at: str = ""


@dataclass
class IntelligenceEvent:
    """Canonical intelligence event record."""

    id: str
    title: str
    summary: str
    category: str
    subcategory: str = ""
    project: str = UNKNOWN
    token: str = UNKNOWN
    blockchain: str = UNKNOWN
    source: str = ""
    source_url: str = ""
    source_type: str = "rss"
    published_at: str = ""
    discovered_at: str = ""
    confidence: str = Confidence.UNCONFIRMED.value
    importance: int = 40
    sentiment: str = "neutral"
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = EventStatus.ACTIVE.value
    created_at: str = ""
    discovery_latency_seconds: Optional[float] = None
    related_sources: list[RelatedSource] = field(default_factory=list)
    fingerprint: str = ""
    cluster_id: str = ""
    source_tier: int = int(SourceTier.UNVERIFIED)
    why_it_matters: str = ""
    what_happened: str = ""
    airdrop_signal_status: str = ""
    is_demo: bool = False
    raw_text: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = utc_now_iso()
        if not self.discovered_at:
            self.discovered_at = self.created_at
        if not self.fingerprint:
            self.fingerprint = content_fingerprint(self.title, self.source_url, self.summary)
        if not self.cluster_id:
            self.cluster_id = cluster_key(self.title, self.project, self.category)
        if not self.what_happened:
            self.what_happened = self.summary or self.title
        if self.is_demo and self.status == EventStatus.ACTIVE.value:
            self.status = EventStatus.DEMO.value

    @property
    def importance_band(self) -> str:
        return importance_band(self.importance).value

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["importance_band"] = self.importance_band
        d["entities_json"] = json.dumps(self.entities)
        d["tags_json"] = json.dumps(self.tags)
        d["related_sources_json"] = json.dumps([asdict(r) for r in self.related_sources])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "IntelligenceEvent":
        entities = row.get("entities")
        tags = row.get("tags")
        related = row.get("related_sources")
        if isinstance(entities, str):
            try:
                entities = json.loads(entities or "[]")
            except json.JSONDecodeError:
                entities = []
        if isinstance(tags, str):
            try:
                tags = json.loads(tags or "[]")
            except json.JSONDecodeError:
                tags = []
        related_list: list[RelatedSource] = []
        if isinstance(related, str):
            try:
                related = json.loads(related or "[]")
            except json.JSONDecodeError:
                related = []
        if isinstance(related, list):
            for item in related:
                if isinstance(item, dict):
                    related_list.append(
                        RelatedSource(
                            name=item.get("name", ""),
                            url=item.get("url", ""),
                            tier=int(item.get("tier", 5)),
                            published_at=item.get("published_at", ""),
                        )
                    )
        return cls(
            id=str(row.get("id") or uuid4()),
            title=row.get("title") or "",
            summary=row.get("summary") or "",
            category=row.get("category") or EventCategory.BREAKING.value,
            subcategory=row.get("subcategory") or "",
            project=row.get("project") or UNKNOWN,
            token=row.get("token") or UNKNOWN,
            blockchain=row.get("blockchain") or UNKNOWN,
            source=row.get("source") or "",
            source_url=row.get("source_url") or "",
            source_type=row.get("source_type") or "rss",
            published_at=row.get("published_at") or "",
            discovered_at=row.get("discovered_at") or "",
            confidence=row.get("confidence") or Confidence.UNCONFIRMED.value,
            importance=int(row.get("importance") or 40),
            sentiment=row.get("sentiment") or "neutral",
            entities=list(entities or []),
            tags=list(tags or []),
            status=row.get("status") or EventStatus.ACTIVE.value,
            created_at=row.get("created_at") or "",
            discovery_latency_seconds=row.get("discovery_latency_seconds"),
            related_sources=related_list,
            fingerprint=row.get("fingerprint") or "",
            cluster_id=row.get("cluster_id") or "",
            source_tier=int(row.get("source_tier") or 5),
            why_it_matters=row.get("why_it_matters") or "",
            what_happened=row.get("what_happened") or "",
            airdrop_signal_status=row.get("airdrop_signal_status") or "",
            is_demo=bool(row.get("is_demo")),
            raw_text=row.get("raw_text") or "",
        )


@dataclass
class FundingRecord:
    id: str
    project: str
    amount: str = NOT_DISCLOSED
    currency: str = "USD"
    round_type: str = UNKNOWN
    announced_at: str = ""
    source_url: str = ""
    confidence: str = Confidence.UNCONFIRMED.value
    notes: str = ""
    is_demo: bool = False
    created_at: str = ""
    investors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = utc_now_iso()


@dataclass
class CandidateProject:
    id: str
    name: str
    status: str = CandidateProjectStatus.DISCOVERED.value
    blockchain: str = UNKNOWN
    website: str = ""
    notes: str = ""
    source_event_id: str = ""
    is_demo: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


@dataclass
class RawDocument:
    """Pre-normalize ingestion unit."""

    title: str
    body: str = ""
    source_name: str = ""
    source_url: str = ""
    source_type: str = "rss"
    source_tier: int = int(SourceTier.UNVERIFIED)
    published_at: str = ""
    discovered_at: str = field(default_factory=utc_now_iso)
    is_demo: bool = False
    meta: dict[str, Any] = field(default_factory=dict)
