"""INGEST stage — pull RawDocuments from source adapters. Soft-fail per source."""
from __future__ import annotations

from typing import Optional, Sequence

from mccc.intelligence.adapters.base import BaseAdapter
from mccc.intelligence.adapters.demo_adapter import DemoAdapter
from mccc.intelligence.adapters.rss_adapter import RssAdapter
from mccc.intelligence.schema import RawDocument
from mccc.intelligence.source_service import SourceDefinition, SourceService


class IngestionService:
    def __init__(self, source_service: Optional[SourceService] = None) -> None:
        self.sources = source_service or SourceService()

    def adapter_for(self, source: SourceDefinition) -> BaseAdapter:
        if source.source_type == "demo":
            return DemoAdapter(source)
        if source.source_type == "rss":
            return RssAdapter(source)
        # stub / unknown → empty adapter behaviour via DemoAdapter disabled pattern
        return _EmptyAdapter(source)

    def ingest(
        self,
        *,
        source_keys: Optional[Sequence[str]] = None,
        include_demo: bool = True,
        include_live_rss: bool = False,
        limit_per_source: int = 15,
    ) -> list[RawDocument]:
        """Fetch raw docs. Live RSS off by default in offline/dev; DEMO always available."""
        out: list[RawDocument] = []
        for src in self.sources.list_sources(enabled_only=True):
            if source_keys is not None and src.key not in source_keys:
                continue
            if src.source_type == "demo" and not include_demo:
                continue
            if src.source_type == "rss" and not include_live_rss:
                continue
            adapter = self.adapter_for(src)
            try:
                docs = list(adapter.fetch(limit=limit_per_source))
            except Exception:
                docs = []
            out.extend(docs)
        return out


class _EmptyAdapter(BaseAdapter):
    """Stub for unknown source_type — returns nothing (build for real providers later)."""

    def fetch(self, limit: int = 20) -> Sequence[RawDocument]:
        return []
