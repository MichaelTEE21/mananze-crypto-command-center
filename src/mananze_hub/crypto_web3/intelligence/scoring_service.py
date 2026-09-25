"""SCORE stage — confidence + importance 0–100 from source tier, category, signals."""
from __future__ import annotations

from dataclasses import dataclass

from mccc.intelligence.schema import (
    Confidence,
    EventCategory,
    SourceTier,
    importance_band,
)


@dataclass
class ScoreResult:
    confidence: str
    importance: int
    importance_band: str
    sentiment: str = "neutral"


_CATEGORY_BASE = {
    EventCategory.BREAKING.value: 70,
    EventCategory.FUNDING.value: 55,
    EventCategory.AIRDROP_SIGNALS.value: 50,
    EventCategory.TOKEN_EVENTS.value: 55,
    EventCategory.NEW_PROJECTS.value: 45,
    EventCategory.TECHNOLOGY.value: 50,
    EventCategory.NARRATIVES.value: 40,
    EventCategory.RWA.value: 55,
}


class ScoringService:
    def score(
        self,
        *,
        source_tier: int,
        category: str,
        is_demo: bool = False,
        has_source_url: bool = False,
        airdrop_signal_status: str = "",
        cluster_size: int = 1,
    ) -> ScoreResult:
        tier = int(source_tier or 5)
        base = _CATEGORY_BASE.get(category, 40)
        # Tier contribution: T1=+25 … T5=+0
        tier_boost = max(0, (5 - tier) * 6)
        url_boost = 5 if has_source_url else 0
        cluster_boost = min(10, max(0, cluster_size - 1) * 3)
        importance = max(0, min(100, base + tier_boost + url_boost + cluster_boost))

        if is_demo:
            # DEMO never claims VERIFIED / CRITICAL live confidence
            confidence = Confidence.UNCONFIRMED.value
            importance = min(importance, 55)
        else:
            confidence = self._confidence_from_tier(tier, has_source_url)

        if category == EventCategory.AIRDROP_SIGNALS.value:
            status = (airdrop_signal_status or "").upper()
            if status == "RUMOR":
                confidence = Confidence.UNCONFIRMED.value
                importance = min(importance, 45)
            elif status == "UNCONFIRMED":
                confidence = Confidence.LOW.value if not is_demo else Confidence.UNCONFIRMED.value

        return ScoreResult(
            confidence=confidence,
            importance=importance,
            importance_band=importance_band(importance).value,
            sentiment="neutral",
        )

    def _confidence_from_tier(self, tier: int, has_url: bool) -> str:
        if tier <= int(SourceTier.OFFICIAL) and has_url:
            return Confidence.VERIFIED.value
        if tier <= int(SourceTier.MAJOR_NEWS) and has_url:
            return Confidence.HIGH.value
        if tier <= int(SourceTier.AGGREGATOR):
            return Confidence.MEDIUM.value
        if tier <= int(SourceTier.SOCIAL):
            return Confidence.LOW.value
        return Confidence.UNCONFIRMED.value
