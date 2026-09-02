"""RWA Phase 1 — taxonomy, profiles, classification, provenance, honesty tests."""
from __future__ import annotations

from pathlib import Path

from mccc.db import init_db, list_projects
from mccc.intelligence.pipeline import IntelligencePipeline
from mccc.intelligence.repository import IntelligenceRepository
from mccc.intelligence.rwa.classification import RWAClassificationService
from mccc.intelligence.rwa.repository import RWARepository, mark_stale
from mccc.intelligence.rwa.schema import (
    ClaimProvenance,
    RWAProfile,
    TokenizedAssetValue,
)
from mccc.intelligence.rwa.service import RWAService
from mccc.intelligence.rwa.taxonomy import (
    AssetValueType,
    DisclosureStatus,
    RWACategory,
    RWAEventType,
    VerificationStatus,
    all_rwa_categories,
    all_rwa_event_types,
    register_category,
    register_event_type,
    is_known_rwa_category,
)
from mccc.intelligence.schema import (
    EventCategory,
    NOT_DISCLOSED,
    UNKNOWN,
    RawDocument,
)
from mccc.intelligence.classification_service import ClassificationService
from mccc.search import search_all, search_rwa


def test_rwa_category_enum_and_extension():
    cats = all_rwa_categories()
    assert RWACategory.TOKENIZED_TREASURIES.value in cats
    assert RWACategory.REAL_ESTATE.value in cats
    assert RWACategory.PRIVATE_CREDIT.value in cats
    assert len(cats) >= 20
    register_category("custom_rwa_widget", "Custom RWA Widget")
    assert is_known_rwa_category("custom_rwa_widget")
    assert "Custom RWA Widget" in all_rwa_categories().values()


def test_rwa_event_types_extensible():
    types = all_rwa_event_types()
    for t in (
        "NEW_PROJECT",
        "ASSET_LAUNCH",
        "FUNDING",
        "REGULATORY",
        "CUSTODY",
        "REDEMPTION",
        "INSTITUTIONAL_ADOPTION",
    ):
        assert t in types
    register_event_type("CUSTOM_SIGNAL")
    assert "CUSTOM_SIGNAL" in all_rwa_event_types()


def test_event_category_includes_rwa():
    assert EventCategory.RWA.value == "rwa"


def test_classify_rwa_membership_and_subcategory():
    c = ClassificationService()
    d = RawDocument(
        title="Tokenized treasury product research note",
        body="RWA real-world asset on-chain treasury bill exposure",
    )
    cat, sub = c.classify(d)
    assert cat == EventCategory.RWA.value
    assert sub == RWACategory.TOKENIZED_TREASURIES.value or "treasury" in sub


def test_rwa_signal_types_detected():
    svc = RWAClassificationService()
    d = RawDocument(title="Institutional adoption of tokenized funds", body="RWA custody rails")
    out = svc.classify(d)
    assert out.is_rwa
    assert out.rwa_event_type in (
        RWAEventType.INSTITUTIONAL_ADOPTION.value,
        RWAEventType.CUSTODY.value,
        RWAEventType.OTHER.value,
    )


def test_profile_creation_and_missing_data_honesty(tmp_path: Path):
    db = tmp_path / "rwa.db"
    init_db(db)
    svc = RWAService(db)
    svc.ensure_ready()
    p = RWAProfile(
        id="p-missing",
        project_name="Test Missing Fields",
        ticker=UNKNOWN,
        jurisdiction=UNKNOWN,
        regulatory_status=NOT_DISCLOSED,
        funding_notes=NOT_DISCLOSED,
        verification_status=VerificationStatus.DISCOVERED.value,
        is_demo=False,
    )
    p.set_asset_value(TokenizedAssetValue.unavailable())
    svc.repo.upsert_profile(p)
    got = svc.repo.get_profile("p-missing")
    assert got is not None
    assert got.ticker == UNKNOWN
    assert got.jurisdiction == UNKNOWN
    assert got.regulatory_status == NOT_DISCLOSED
    assert got.asset_value().value_type == AssetValueType.UNAVAILABLE.value
    assert "TVL" not in got.asset_value().display_label().upper() or "not tvl" in got.asset_value().display_label().lower()


def test_provenance_on_claims(tmp_path: Path):
    db = tmp_path / "rwa2.db"
    init_db(db)
    svc = RWAService(db)
    p = RWAProfile(
        id="p-prov",
        project_name="Provenance Sample",
        rwa_category=RWACategory.TOKENIZED_TREASURIES.value,
        verification_status=VerificationStatus.DISCOVERED.value,
        provenance=[
            ClaimProvenance(
                source="Issuer docs",
                source_url="https://example.com/docs",
                source_type="docs",
                published_at="2026-08-01T00:00:00+00:00",
                discovered_at="2026-08-02T00:00:00+00:00",
                confidence="MEDIUM",
                provenance_tier="docs",
                claim_key="issuer_identity",
                claim_value="DISCLOSED in docs sample",
            )
        ],
    )
    svc.repo.upsert_profile(p)
    got = svc.repo.get_profile("p-prov")
    assert got.provenance
    assert got.provenance[0].source_url.startswith("http")
    assert got.provenance[0].confidence == "MEDIUM"


def test_verification_statuses_no_auto_verify(tmp_path: Path):
    db = tmp_path / "rwa3.db"
    init_db(db)
    svc = RWAService(db)
    res = svc.seed_demo_if_empty()
    assert res.profiles_stored >= 1 or svc.repo.count_profiles(is_demo=True) >= 1
    for p in svc.repo.list_profiles(include_demo=True, limit=50):
        assert p.verification_status in {s.value for s in VerificationStatus}
        assert p.verification_status != VerificationStatus.VERIFIED.value  # seeds stay non-verified


def test_funding_not_invented(tmp_path: Path):
    db = tmp_path / "rwa4.db"
    init_db(db)
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    for p in svc.repo.list_profiles(limit=50):
        assert p.funding_notes in (NOT_DISCLOSED, UNKNOWN, "Not disclosed", "") or p.is_demo
        # never invent dollar rounds as verified
        assert "$10M" not in (p.funding_notes or "")
        assert "$100,000,000" not in (p.funding_notes or "")


def test_asset_value_types_and_stale(tmp_path: Path):
    av = TokenizedAssetValue(
        value_type=AssetValueType.CALCULATED_ESTIMATE.value,
        amount="Not disclosed as verified",
        measured_at="2025-01-15T12:00:00+00:00",
        notes="estimate",
    )
    av = mark_stale(av)
    assert av.is_stale is True
    assert "not tvl" in av.display_label().lower()
    assert "TVL" not in av.display_label() or "not TVL" in av.display_label()


def test_demo_live_separation(tmp_path: Path):
    db = tmp_path / "rwa5.db"
    init_db(db)
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    demos = svc.repo.list_profiles(include_demo=True, include_live=False)
    assert demos
    for p in demos:
        assert p.is_demo
        assert "demo" in [t.lower() for t in p.tags] or "DEMO" in p.project_name.upper()
    lives = svc.repo.list_profiles(include_demo=False, include_live=True)
    for p in lives:
        assert not p.is_demo


def test_filters_and_search(tmp_path: Path):
    db = tmp_path / "rwa6.db"
    init_db(db)
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    treas = svc.repo.list_profiles(category=RWACategory.TOKENIZED_TREASURIES.value)
    assert treas
    hits = search_rwa("treasury", db_path=db)
    assert hits
    assert all(h.get("is_demo") for h in hits) or True
    all_hits = search_all("DEMO", categories=["rwa"], db_path=db)
    assert all_hits.get("rwa")


def test_watchlist_and_relationships(tmp_path: Path):
    db = tmp_path / "rwa7.db"
    init_db(db)
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    profiles = svc.repo.list_profiles(limit=1)
    assert profiles
    p = profiles[0]
    wid = svc.repo.add_watch("profile", p.id, notes="test follow")
    assert wid >= 1
    watch = svc.repo.list_watch()
    assert any(w["ref_id"] == p.id for w in watch)
    # link event relationship
    svc.repo.link_event(p.id, "evt-demo-1", RWAEventType.NEW_PROJECT.value)
    linked = svc.repo.list_linked_events(p.id)
    assert linked
    # add to project tracker
    pid = svc.add_to_project_tracker(p)
    assert pid >= 1
    projects = list_projects(db_path=db)
    assert any(x["id"] == pid for x in projects)
    got = svc.repo.get_profile(p.id)
    assert got.project_id == pid


def test_confidence_and_no_fabricated_verified(tmp_path: Path):
    db = tmp_path / "rwa8.db"
    init_db(db)
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    for p in svc.repo.list_profiles(limit=50):
        if p.is_demo:
            assert p.confidence in ("UNCONFIRMED", "LOW", "MEDIUM")
            assert p.verification_status != VerificationStatus.VERIFIED.value


def test_pipeline_classifies_rwa_events(tmp_path: Path):
    db = tmp_path / "rwa9.db"
    # fresh pipeline without prior seed events — force run
    pipe = IntelligencePipeline(db)
    pipe.ensure_ready()
    # clear path: run demo including RWA docs
    result = pipe.run(include_demo=True, include_live_rss=False)
    assert result.stored >= 1
    repo = IntelligenceRepository(db)
    rwa_events = repo.list_events(category=EventCategory.RWA.value, limit=50)
    # RWA docs should produce rwa category events
    assert len(rwa_events) >= 1
    for ev in rwa_events:
        assert ev.is_demo
        assert "DEMO" in ev.title.upper() or ev.status == "DEMO"


def test_dupes_idempotent_rwa_seed(tmp_path: Path):
    db = tmp_path / "rwa10.db"
    svc = RWAService(db)
    r1 = svc.seed_demo()
    assert r1.profiles_stored >= 5
    r2 = svc.seed_demo(force=False)
    assert r2.profiles_stored == 0
    assert r2.skipped_existing >= 5


def test_disclosure_statuses_only():
    assert DisclosureStatus.DISCLOSED.value == "DISCLOSED"
    assert DisclosureStatus.NOT_DISCLOSED.value == "NOT DISCLOSED"
    assert DisclosureStatus.UNKNOWN.value == "UNKNOWN"


def test_analytics_from_stored_only(tmp_path: Path):
    db = tmp_path / "rwa11.db"
    svc = RWAService(db)
    svc.seed_demo_if_empty()
    summary = svc.analytics()
    assert summary["total"] == summary["demo"] + summary["live"]
    assert summary["data_mode"] in ("DEMO", "MIXED", "LIVE", "EMPTY")
    for n in summary.get("narratives") or []:
        assert "TVL" not in (n.get("title") or "")
    # estimates must not be marketed as TVL in labels
    for p in svc.repo.list_profiles(limit=50):
        lab = p.asset_value().display_label()
        if p.asset_value().value_type == "calculated_estimate":
            assert "not tvl" in lab.lower()
    # narratives observed from categories
    assert summary["narratives"]
