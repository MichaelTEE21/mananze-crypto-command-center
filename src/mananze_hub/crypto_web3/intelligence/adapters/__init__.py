"""Ingestion adapters — RSS / DEMO / stubs only in Phase 1."""
from mananze_hub.crypto_web3.intelligence.adapters.base import BaseAdapter
from mananze_hub.crypto_web3.intelligence.adapters.demo_adapter import DemoAdapter
from mananze_hub.crypto_web3.intelligence.adapters.rss_adapter import RssAdapter, parse_feed_xml

__all__ = ["BaseAdapter", "DemoAdapter", "RssAdapter", "parse_feed_xml"]
