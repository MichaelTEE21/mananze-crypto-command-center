"""Ingestion adapters — RSS / DEMO / stubs only in Phase 1."""
from mccc.intelligence.adapters.base import BaseAdapter
from mccc.intelligence.adapters.demo_adapter import DemoAdapter
from mccc.intelligence.adapters.rss_adapter import RssAdapter, parse_feed_xml

__all__ = ["BaseAdapter", "DemoAdapter", "RssAdapter", "parse_feed_xml"]
