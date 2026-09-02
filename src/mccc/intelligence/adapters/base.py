"""Base adapter interface for intelligence ingestion."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from mccc.intelligence.schema import RawDocument
from mccc.intelligence.source_service import SourceDefinition


class BaseAdapter(ABC):
    source: SourceDefinition

    def __init__(self, source: SourceDefinition) -> None:
        self.source = source

    @abstractmethod
    def fetch(self, limit: int = 20) -> Sequence[RawDocument]:
        """Return raw documents. Must soft-fail (empty list) on network/errors."""
