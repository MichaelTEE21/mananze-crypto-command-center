"""RWAService — seed, search, analytics, project linking, pipeline bridge."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from mccc.db import add_project
from mccc.intelligence.rwa.classification import RWAClassificationService
from mccc.intelligence.rwa.demo_seed import (
    DEMO_RWA_NARRATIVES,
    build_demo_profiles,
    build_demo_raw_documents,
)
from mccc.intelligence.rwa.repository import RWARepository
from mccc.intelligence.rwa.schema import RWAProfile
from mccc.intelligence.rwa.taxonomy import (
    RWA_DISCLAIMER,
    TOP_LEVEL_CATEGORY,
    VerificationStatus,
    all_rwa_categories,
)
from mccc.intelligence.schema import UNKNOWN


@dataclass
class RWASeedResult:
    profiles_stored: int = 0
    skipped_existing: int = 0
    narratives_stored: int = 0
    errors: list[str] = field(default_factory=list)


class RWAService:
    """High-level RWA vertical API over repository + classification."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path
        self.repo = RWARepository(db_path)
        self.classifier = RWAClassificationService()

    def ensure_ready(self) -> None:
        self.repo.ensure_schema()

    def seed_demo_if_empty(self) -> RWASeedResult:
        """Idempotent DEMO seed — never presents as live."""
        self.ensure_ready()
        result = RWASeedResult()
        if self.repo.count_profiles(is_demo=True) > 0:
            return result
        return self.seed_demo(force=False)

    def seed_demo(self, *, force: bool = False) -> RWASeedResult:
        self.ensure_ready()
        result = RWASeedResult()
        for profile in build_demo_profiles():
            existing = self.repo.find_by_name(profile.project_name)
            if existing and not force:
                result.skipped_existing += 1
                continue
            if existing and force:
                profile.id = existing.id
            try:
                self.repo.upsert_profile(profile)
                result.profiles_stored += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(str(exc))

        try:
            from mccc.intelligence.repository import IntelligenceRepository

            irepo = IntelligenceRepository(self.db_path)
            irepo.ensure_schema()
            for n in DEMO_RWA_NARRATIVES:
                irepo.upsert_narrative(
                    slug=n["slug"],
                    title=n["title"],
                    summary=n["summary"],
                    tags=list(n.get("tags") or []),
                    is_demo=True,
                    heat=12,
                )
                result.narratives_stored += 1
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"narratives: {exc}")
        return result

    def demo_raw_documents(self):
        return build_demo_raw_documents()

    def list_categories(self) -> dict[str, str]:
        return all_rwa_categories()

    def search(
        self,
        q: str,
        *,
        category: Optional[str] = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        profiles = self.repo.list_profiles(q=q, category=category, limit=limit)
        out = []
        for p in profiles:
            d = p.to_dict()
            d["search_category"] = "rwa"
            d["top_level"] = TOP_LEVEL_CATEGORY
            out.append(d)
        return out

    def analytics(self) -> dict[str, Any]:
        self.ensure_ready()
        summary = self.repo.analytics_summary(include_demo=True)
        summary["disclaimer"] = RWA_DISCLAIMER
        summary["narratives"] = self.repo.observed_narratives()
        return summary

    def add_to_project_tracker(self, profile: RWAProfile) -> int:
        """Create a Project Tracker row linked to this RWA profile (DISCOVERED)."""
        name = profile.project_name
        if profile.is_demo and not str(name).upper().startswith("DEMO"):
            name = f"DEMO: {name}"
        notes = (
            f"From RWA Intelligence · profile {profile.id}\n"
            f"Category: {profile.rwa_category or UNKNOWN}\n"
            f"{profile.description}\n"
            f"{'DEMO / SYNTHETIC' if profile.is_demo else ''}"
        )
        pid = add_project(
            name=name,
            chain=profile.blockchain if profile.blockchain != UNKNOWN else "",
            status="discovered",
            notes=notes,
            priority=2,
            db_path=self.db_path,
            category="RWA",
            ticker=profile.ticker if profile.ticker != UNKNOWN else "",
            website=profile.website_url or "",
            docs=profile.docs_url or "",
            description=profile.description[:500],
            launch_status=profile.launch_status,
            token_status=profile.token_status,
            tags="rwa,demo" if profile.is_demo else "rwa",
        )
        self.repo.link_project(profile.id, pid)
        return pid

    def upsert_from_event(
        self,
        *,
        project_name: str,
        rwa_category: str = "",
        blockchain: str = UNKNOWN,
        event_id: str = "",
        rwa_event_type: str = "OTHER",
        is_demo: bool = False,
        source_url: str = "",
        description: str = "",
    ) -> str:
        """Create or attach an RWA profile from a classified intelligence event."""
        self.ensure_ready()
        name = (project_name or "").strip() or UNKNOWN
        if name == UNKNOWN:
            if not is_demo:
                return ""
            name = (
                f"DEMO Unnamed RWA {event_id[:8]}"
                if event_id
                else f"DEMO Unnamed RWA {uuid4().hex[:8]}"
            )

        existing = self.repo.find_by_name(name)
        if existing:
            if event_id:
                self.repo.link_event(existing.id, event_id, rwa_event_type)
            return existing.id

        profile = RWAProfile(
            id=str(uuid4()),
            project_name=name,
            rwa_category=rwa_category,
            blockchain=blockchain or UNKNOWN,
            description=description or "",
            source_event_id=event_id,
            is_demo=is_demo,
            verification_status=VerificationStatus.DISCOVERED.value,
            confidence="UNCONFIRMED",
            tags=["rwa"] + (["demo", "synthetic"] if is_demo else []),
        )
        if source_url and source_url.startswith("http"):
            profile.website_url = source_url
        self.repo.upsert_profile(profile)
        if event_id:
            self.repo.link_event(profile.id, event_id, rwa_event_type)
        return profile.id
