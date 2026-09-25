"""NORMALIZE stage — clean titles/bodies, strip HTML-ish noise, clamp fields."""
from __future__ import annotations

import html
import re
from typing import Optional

from mccc.intelligence.schema import (
    UNKNOWN,
    RawDocument,
    utc_now_iso,
)


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_markup(text: str) -> str:
    if not text:
        return ""
    t = html.unescape(text)
    t = _TAG_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


class NormalizationService:
    def normalize(self, doc: RawDocument) -> RawDocument:
        title = strip_markup(doc.title)[:500] or "(untitled)"
        body = strip_markup(doc.body)[:8000]
        url = (doc.source_url or "").strip()
        # Never invent URLs
        if url and not (url.startswith("http://") or url.startswith("https://")):
            url = ""
        published = (doc.published_at or "").strip()
        discovered = (doc.discovered_at or "").strip() or utc_now_iso()
        meta = dict(doc.meta or {})
        # Preserve DEMO flag; do not upgrade demo → live
        is_demo = bool(doc.is_demo) or (doc.source_type == "demo")
        if is_demo and not title.upper().startswith("[DEMO]") and "DEMO" not in title.upper():
            title = f"[DEMO] {title}"
        return RawDocument(
            title=title,
            body=body,
            source_name=(doc.source_name or "").strip() or UNKNOWN,
            source_url=url,
            source_type=(doc.source_type or "rss").strip(),
            source_tier=int(doc.source_tier or 5),
            published_at=published,
            discovered_at=discovered,
            is_demo=is_demo,
            meta=meta,
        )

    def normalize_many(self, docs: list[RawDocument]) -> list[RawDocument]:
        return [self.normalize(d) for d in docs]
