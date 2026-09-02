"""Classification + normalize filter behaviour."""
from __future__ import annotations

from mccc.intelligence.classification_service import ClassificationService
from mccc.intelligence.normalization_service import NormalizationService
from mccc.intelligence.schema import EventCategory, RawDocument
from mccc.intelligence.source_service import SourceService, SourceTier


def test_classify_funding_and_airdrop():
    c = ClassificationService()
    d1 = RawDocument(title="Protocol raises series A", body="funding round")
    assert c.classify(d1)[0] == EventCategory.FUNDING.value
    d2 = RawDocument(title="Points program eligibility", body="airdrop season")
    assert c.classify(d2)[0] == EventCategory.AIRDROP_SIGNALS.value


def test_normalize_marks_demo_and_strips_bad_url():
    n = NormalizationService()
    doc = n.normalize(
        RawDocument(
            title="Plain title",
            body="<b>Hello</b> world",
            source_url="javascript:alert(1)",
            source_type="demo",
            is_demo=True,
        )
    )
    assert doc.title.upper().startswith("[DEMO]")
    assert doc.source_url == ""
    assert "Hello world" in doc.body
    assert "<b>" not in doc.body


def test_source_tiers_registered():
    svc = SourceService()
    demo = svc.get("demo_seed")
    assert demo is not None
    assert demo.tier == SourceTier.UNVERIFIED
    assert svc.tier_for("missing") == SourceTier.UNVERIFIED
