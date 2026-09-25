"""RSS / Atom adapter using stdlib + requests. Soft-fails; respects min interval via caller."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Sequence
from urllib.parse import urlparse

import requests

from mccc.intelligence.adapters.base import BaseAdapter
from mccc.intelligence.schema import RawDocument, SourceTier, utc_now_iso


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def parse_feed_xml(xml_text: str, source_name: str, source_tier: int, limit: int = 20) -> list[RawDocument]:
    """Parse RSS 2.0 or Atom XML into RawDocuments. No hallucination — empty fields stay empty."""
    root = ET.fromstring(xml_text)
    docs: list[RawDocument] = []
    # RSS channel/item
    items = [e for e in root.iter() if _local(e.tag) == "item"]
    if not items:
        items = [e for e in root.iter() if _local(e.tag) == "entry"]
    for item in items[:limit]:
        title = ""
        link = ""
        summary = ""
        published = ""
        for child in list(item):
            name = _local(child.tag)
            if name == "title" and not title:
                title = _text(child)
            elif name == "link":
                href = child.attrib.get("href") or _text(child)
                if href and not link:
                    link = href.strip()
            elif name in ("description", "summary", "content") and not summary:
                summary = _text(child)
            elif name in ("pubDate", "published", "updated") and not published:
                published = _text(child)
        if not title and not summary:
            continue
        docs.append(
            RawDocument(
                title=title or "(untitled)",
                body=summary,
                source_name=source_name,
                source_url=link,
                source_type="rss",
                source_tier=source_tier,
                published_at=published,
                discovered_at=utc_now_iso(),
                is_demo=False,
            )
        )
    return docs


class RssAdapter(BaseAdapter):
    timeout_seconds: float = 12.0

    def fetch(self, limit: int = 20) -> Sequence[RawDocument]:
        url = (self.source.feed_url or "").strip()
        if not url:
            return []
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return []
        try:
            resp = requests.get(
                url,
                timeout=self.timeout_seconds,
                headers={"User-Agent": "MCCC-Intelligence/1.0 (+research; respectful RSS client)"},
            )
            if resp.status_code != 200 or not resp.text:
                return []
            return parse_feed_xml(
                resp.text,
                source_name=self.source.name,
                source_tier=int(self.source.tier),
                limit=limit,
            )
        except Exception:
            return []
