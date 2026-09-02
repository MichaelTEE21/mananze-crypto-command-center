"""DEMO / SAMPLE adapter — never presented as live verified intelligence."""
from __future__ import annotations

from typing import Sequence

from mccc.intelligence.demo_feed import DEMO_RAW_DOCUMENTS
from mccc.intelligence.schema import RawDocument
from mccc.intelligence.adapters.base import BaseAdapter


class DemoAdapter(BaseAdapter):
    def fetch(self, limit: int = 20) -> Sequence[RawDocument]:
        docs = list(DEMO_RAW_DOCUMENTS)
        try:
            from mccc.intelligence.rwa.demo_seed import build_demo_raw_documents

            docs.extend(build_demo_raw_documents())
        except Exception:
            pass
        return docs[: max(0, limit)]
