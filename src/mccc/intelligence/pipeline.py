"""Intelligence pipeline orchestrator.

Exact stage order (Phase 1 non-negotiable):
  INGEST → NORMALIZE → DEDUPE → CLASSIFY → EXTRACT → SCORE → SUMMARIZE → STORE

FILTER before expensive summarize is enforced: we only summarize docs that
survived dedupe and classification. Summarization is extractive unless AI key set.
This is an intelligence engine — not a chatbot. The assistant may later explain
events from this DB; it does not replace discovery/structuring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence
from uuid import uuid4

from mccc.intelligence.classification_service import ClassificationService
from mccc.intelligence.deduplication_service import DeduplicationService
from mccc.intelligence.extraction_service import ExtractionService
from mccc.intelligence.ingestion_service import IngestionService
from mccc.intelligence.normalization_service import NormalizationService
from mccc.intelligence.repository import IntelligenceRepository, compute_discovery_latency_seconds
from mccc.intelligence.schema import (
    CandidateProject,
    CandidateProjectStatus,
    EventCategory,
    EventStatus,
    FundingRecord,
    IntelligenceEvent,
    NOT_DISCLOSED,
    UNKNOWN,
    utc_now_iso,
)
from mccc.intelligence.scoring_service import ScoringService
from mccc.intelligence.source_service import SourceService
from mccc.intelligence.summarization_service import SummarizationService
from mccc.intelligence.demo_feed import DEMO_NARRATIVES
from mccc.intelligence.rwa.service import RWAService
from mccc.intelligence.rwa.classification import RWAClassificationService


@dataclass
class PipelineResult:
    run_id: str
    ingested: int = 0
    normalized: int = 0
    after_dedupe: int = 0
    stored: int = 0
    deduped_dropped: int = 0
    skipped_existing: int = 0
    errors: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)


class IntelligencePipeline:
    """SOURCE→INGEST→NORMALIZE→DEDUPE→CLASSIFY→EXTRACT→SCORE→SUMMARIZE→STORE."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path
        self.repo = IntelligenceRepository(db_path)
        self.sources = SourceService()
        self.ingestion = IngestionService(self.sources)
        self.normalizer = NormalizationService()
        self.deduper = DeduplicationService()
        self.classifier = ClassificationService()
        self.extractor = ExtractionService()
        self.scorer = ScoringService()
        self.summarizer = SummarizationService()
        self.rwa = RWAService(db_path)
        self.rwa_classifier = RWAClassificationService()

    def ensure_ready(self) -> None:
        self.repo.ensure_schema()
        self.rwa.ensure_ready()
        for s in self.sources.list_sources():
            self.repo.upsert_source_row(
                s.key, s.name, int(s.tier), s.source_type,
                feed_url=s.feed_url, homepage=s.homepage, enabled=s.enabled,
                min_interval_seconds=s.min_interval_seconds, notes=s.notes,
            )

    def run(
        self,
        *,
        include_demo: bool = True,
        include_live_rss: bool = False,
        source_keys: Optional[Sequence[str]] = None,
        limit_per_source: int = 25,
    ) -> PipelineResult:
        self.ensure_ready()
        keys = list(source_keys) if source_keys else [s.key for s in self.sources.list_sources(enabled_only=True)]
        run_id = self.repo.start_run(keys)
        result = PipelineResult(run_id=run_id)
        try:
            # INGEST
            raw = self.ingestion.ingest(
                source_keys=source_keys,
                include_demo=include_demo,
                include_live_rss=include_live_rss,
                limit_per_source=limit_per_source,
            )
            result.ingested = len(raw)

            # NORMALIZE
            normalized = self.normalizer.normalize_many(raw)
            result.normalized = len(normalized)

            # DEDUPE (in-batch)
            dedupe = self.deduper.dedupe_raw(normalized)
            result.deduped_dropped = dedupe.dropped
            unique = dedupe.unique_docs
            result.after_dedupe = len(unique)

            existing_fp = self.repo.existing_fingerprints()

            for doc in unique:
                fp = self.deduper.fingerprint(doc)
                if fp in existing_fp:
                    result.skipped_existing += 1
                    continue

                # CLASSIFY
                category, subcategory = self.classifier.classify(doc)

                # EXTRACT
                extracted = self.extractor.extract(doc, category=category)

                # SCORE (pre-summarize — cost control)
                score = self.scorer.score(
                    source_tier=doc.source_tier,
                    category=category,
                    is_demo=doc.is_demo,
                    has_source_url=bool(doc.source_url),
                    airdrop_signal_status=extracted.airdrop_signal_status,
                    cluster_size=len(dedupe.clusters.get(self.deduper.cluster_id(doc), [fp])),
                )

                # SUMMARIZE (only after filter/dedupe/classify)
                summary = self.summarizer.summarize(
                    title=doc.title,
                    body=doc.body,
                    fingerprint=fp,
                    is_demo=doc.is_demo,
                )
                why = self.summarizer.why_it_matters(
                    category=category, project=extracted.project, is_demo=doc.is_demo
                )

                status = EventStatus.DEMO.value if doc.is_demo else EventStatus.ACTIVE.value
                discovered = doc.discovered_at or utc_now_iso()
                latency = compute_discovery_latency_seconds(doc.published_at, discovered)

                event = IntelligenceEvent(
                    id=str(uuid4()),
                    title=doc.title,
                    summary=summary,
                    category=category,
                    subcategory=subcategory,
                    project=extracted.project,
                    token=extracted.token,
                    blockchain=extracted.blockchain,
                    source=doc.source_name,
                    source_url=doc.source_url,
                    source_type=doc.source_type,
                    published_at=doc.published_at,
                    discovered_at=discovered,
                    confidence=score.confidence,
                    importance=score.importance,
                    sentiment=score.sentiment,
                    entities=extracted.entities,
                    tags=extracted.tags,
                    status=status,
                    created_at=utc_now_iso(),
                    discovery_latency_seconds=latency,
                    fingerprint=fp,
                    cluster_id=self.deduper.cluster_id(doc),
                    source_tier=int(doc.source_tier),
                    why_it_matters=why,
                    what_happened=summary or doc.title,
                    airdrop_signal_status=extracted.airdrop_signal_status,
                    is_demo=doc.is_demo,
                    raw_text=doc.body,
                )

                # STORE
                self.repo.upsert_event(event)
                result.event_ids.append(event.id)
                result.stored += 1
                existing_fp.add(fp)

                if category == EventCategory.FUNDING.value:
                    self.repo.add_funding(
                        FundingRecord(
                            id=str(uuid4()),
                            project=extracted.project,
                            amount=extracted.funding_amount or NOT_DISCLOSED,
                            investors=list(extracted.investors),
                            source_url=doc.source_url,
                            confidence=score.confidence,
                            is_demo=doc.is_demo,
                            notes="From intelligence pipeline — verify source.",
                            announced_at=doc.published_at,
                        ),
                        event_id=event.id,
                    )

                if category == EventCategory.NEW_PROJECTS.value and extracted.project != UNKNOWN:
                    self.repo.add_candidate(
                        CandidateProject(
                            id=str(uuid4()),
                            name=extracted.project,
                            status=CandidateProjectStatus.DISCOVERED.value,
                            blockchain=extracted.blockchain,
                            source_event_id=event.id,
                            is_demo=doc.is_demo,
                            notes="Auto-discovered — requires human REVIEW before VERIFIED.",
                        )
                    )

                # RWA vertical: classify + link profile (never auto-VERIFIED)
                rwa_cls = self.rwa_classifier.classify(doc)
                if category == EventCategory.RWA.value or rwa_cls.is_rwa:
                    if not event.tags:
                        event.tags = []
                    if "rwa" not in [t.lower() for t in event.tags]:
                        event.tags = list(event.tags) + ["rwa"]
                        self.repo.upsert_event(event)
                    sub = subcategory or rwa_cls.rwa_category
                    if sub and not event.subcategory:
                        event.subcategory = sub
                        self.repo.upsert_event(event)
                    self.rwa.upsert_from_event(
                        project_name=extracted.project,
                        rwa_category=sub or rwa_cls.rwa_category,
                        blockchain=extracted.blockchain,
                        event_id=event.id,
                        rwa_event_type=rwa_cls.rwa_event_type,
                        is_demo=doc.is_demo,
                        source_url=doc.source_url,
                        description=summary or doc.title,
                    )

            # Seed DEMO narratives once if empty
            if include_demo and not self.repo.list_narratives(limit=1):
                for n in DEMO_NARRATIVES:
                    self.repo.upsert_narrative(
                        slug=n["slug"],
                        title=n["title"],
                        summary=n["summary"],
                        tags=list(n.get("tags") or []),
                        is_demo=True,
                        heat=10,
                    )

            self.repo.finish_run(
                run_id,
                status="ok",
                docs_ingested=result.ingested,
                docs_stored=result.stored,
                docs_deduped=result.deduped_dropped + result.skipped_existing,
                meta={"include_demo": include_demo, "include_live_rss": include_live_rss},
            )
        except Exception as exc:  # noqa: BLE001
            result.errors.append(str(exc))
            self.repo.finish_run(run_id, status="error", error=str(exc))
        return result

    def seed_demo_if_empty(self) -> PipelineResult:
        """Idempotent DEMO seed for offline UI — never presents as live."""
        self.ensure_ready()
        # Always ensure RWA DEMO profiles exist (separate table; labelled)
        try:
            self.rwa.seed_demo_if_empty()
        except Exception:
            pass
        if self.repo.count_events(is_demo=True) > 0:
            return PipelineResult(run_id="skipped", stored=0)
        return self.run(include_demo=True, include_live_rss=False)

    def briefing(self, *, limit: int = 20, include_demo: bool = True) -> list[IntelligenceEvent]:
        """Ranked 'what happened while I was away?' foundation — sourced events only."""
        self.ensure_ready()
        return self.repo.list_events(include_demo=include_demo, include_live=True, limit=limit)
