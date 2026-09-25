"""DEDUPE stage — fingerprint exact match + cluster merge for near-duplicates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mccc.intelligence.schema import (
    IntelligenceEvent,
    RelatedSource,
    RawDocument,
    cluster_key,
    content_fingerprint,
)


@dataclass
class DedupeResult:
    unique_docs: list[RawDocument] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)  # cluster_id -> fingerprints
    dropped: int = 0


class DeduplicationService:
    def fingerprint(self, doc: RawDocument) -> str:
        return content_fingerprint(doc.title, doc.source_url, doc.body)

    def cluster_id(self, doc: RawDocument) -> str:
        project = str((doc.meta or {}).get("project") or "")
        category = str((doc.meta or {}).get("category_hint") or "")
        return cluster_key(doc.title, project, category)

    def dedupe_raw(self, docs: list[RawDocument]) -> DedupeResult:
        seen_fp: set[str] = set()
        unique: list[RawDocument] = []
        clusters: dict[str, list[str]] = {}
        dropped = 0
        for doc in docs:
            fp = self.fingerprint(doc)
            if fp in seen_fp:
                dropped += 1
                cid = self.cluster_id(doc)
                clusters.setdefault(cid, []).append(fp)
                continue
            seen_fp.add(fp)
            unique.append(doc)
            cid = self.cluster_id(doc)
            clusters.setdefault(cid, []).append(fp)
        return DedupeResult(unique_docs=unique, clusters=clusters, dropped=dropped)

    def merge_related_into_event(
        self,
        primary: IntelligenceEvent,
        siblings: list[IntelligenceEvent],
    ) -> IntelligenceEvent:
        """Attach sibling sources onto primary related_sources list (cluster)."""
        existing_urls = {r.url for r in primary.related_sources if r.url}
        if primary.source_url:
            existing_urls.add(primary.source_url)
        for sib in siblings:
            if sib.id == primary.id:
                continue
            url = sib.source_url or ""
            if url and url in existing_urls:
                continue
            primary.related_sources.append(
                RelatedSource(
                    name=sib.source or "",
                    url=url,
                    tier=int(sib.source_tier or 5),
                    published_at=sib.published_at or "",
                )
            )
            if url:
                existing_urls.add(url)
        return primary

    def is_duplicate_of_stored(self, fingerprint: str, existing_fingerprints: set[str]) -> bool:
        return fingerprint in existing_fingerprints
