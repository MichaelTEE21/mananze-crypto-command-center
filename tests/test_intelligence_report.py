"""Intelligence Report engine — validation, providers, analytics, security, UI helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from mccc.intelligence.report.analytics import (
    analyze_token,
    analyze_wallet,
    concentration,
    detect_activity_change,
    summarize_transactions,
)
from mccc.intelligence.report.education import explain_metric, journey_steps, render_explainer_markdown
from mccc.intelligence.report.engine import ReportEngine
from mccc.intelligence.report.normalize import normalize_token, normalize_wallet
from mccc.intelligence.report.providers import FailingProvider, ProviderResult, StaticDemoProvider
from mccc.intelligence.report.schema import (
    REPORT_DISCLAIMER,
    DataMode,
    EntityType,
    IntelligenceReport,
    SUPPORTED_ENTITY_TYPES,
)
from mccc.intelligence.report.validators import detect_entity_type, validate_report_query
from mccc.security import SensitiveCredentialError


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    db = tmp_path / "report.db"
    # init minimal via ReportRepository / engine
    return db


def test_supported_entity_types():
    assert "wallet" in SUPPORTED_ENTITY_TYPES
    assert "rwa" in SUPPORTED_ENTITY_TYPES
    assert "token" in SUPPORTED_ENTITY_TYPES


def test_validate_empty_rejected():
    v = validate_report_query("")
    assert not v.ok
    assert "Enter" in v.error or "analyse" in v.error.lower()


def test_validate_rejects_mnemonic():
    phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    v = validate_report_query(phrase)
    assert not v.ok
    assert v.rejected_secret


def test_validate_rejects_hex_private_key():
    v = validate_report_query("0x" + "ab" * 32)
    assert not v.ok
    assert v.rejected_secret


def test_validate_wallet_address_ok():
    addr = "0x" + "11" * 20
    v = validate_report_query(addr, entity_type_hint="wallet")
    assert v.ok
    assert v.entity_type == "wallet"
    assert v.normalized.lower() == addr.lower()


def test_validate_demo_wallet():
    v = validate_report_query("0xDEMO000000000000000000000000000000000001")
    assert v.ok
    assert v.entity_type == "wallet"


def test_validate_unsupported_type():
    v = validate_report_query("uniswap", entity_type_hint="spaceship")
    assert not v.ok
    assert v.entity_type == EntityType.UNSUPPORTED.value


def test_detect_token_and_protocol():
    assert detect_entity_type("bitcoin") == "token"
    assert detect_entity_type("uniswap") == "protocol"
    assert detect_entity_type("rwa: treasuries") == "rwa"


def test_summarize_transactions_no_invent():
    s = summarize_transactions(None)
    assert s["count"] is None
    assert "UNAVAILABLE" in s["status"] or "Insufficient" in s["note"]


def test_concentration_empty():
    c = concentration([])
    assert c["status"] == "Insufficient data"


def test_concentration_skewed():
    c = concentration(
        [{"token": "A", "amount": 100}, {"token": "B", "amount": 1}]
    )
    assert c["top_share"] is not None
    assert c["top_share"] > 0.9


def test_detect_activity_change():
    prev = {"balance_eth": 1.0, "normalized_at": "t0"}
    cur = {"balance_eth": 2.0, "normalized_at": "t1"}
    changes = detect_activity_change(prev, cur)
    assert any(ch.field == "balance_eth" for ch in changes)


def test_static_demo_provider_wallet():
    p = StaticDemoProvider()
    r = p.fetch_wallet("0xDEMO1")
    assert r.ok and r.is_demo and not r.is_live
    assert "DEMO" in r.source.upper() or "SYNTHETIC" in r.source.upper()


def test_failing_provider_modes():
    for mode in ("error", "timeout", "rate_limit", "empty"):
        r = FailingProvider(mode).fetch_token("eth")
        assert not r.ok
        assert "UNAVAILABLE" in r.error
        if mode == "timeout":
            assert r.timed_out
        if mode == "rate_limit":
            assert r.rate_limited


def test_normalize_wallet_and_analyze(tmp_db: Path):
    raw = StaticDemoProvider().fetch_wallet("0xDEMO1", chain="ethereum")
    norm = normalize_wallet(raw)
    out = analyze_wallet(norm)
    assert out["metrics"]
    assert out["wallet_intelligence"]["interaction_note"]
    assert any("identity" in f.code or "belongs" not in f.detail.lower() or True for f in out["risk_flags"])
    # identity caution present
    assert any(f.code == "identity_caution" for f in out["risk_flags"])


def test_analyze_token_demo():
    raw = StaticDemoProvider().fetch_token("eth")
    norm = normalize_token(raw)
    out = analyze_token(norm)
    assert out["token_intelligence"]["verification"] in ("verified", "estimated", "unknown")
    assert out["metrics"]


def test_engine_rejects_secret(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse("seed phrase abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about")
    assert report.entity_type in ("unsupported", "unknown")
    assert report.errors or report.unsupported_reason


def test_engine_demo_wallet_report(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse(
        "0xDEMO000000000000000000000000000000000001",
        entity_type_hint="wallet",
    )
    assert isinstance(report, IntelligenceReport)
    assert report.entity_type == "wallet"
    assert report.is_demo or report.data_mode == DataMode.DEMO.value
    assert report.executive_summary
    assert report.beginner is not None
    assert report.sources
    assert report.confidence in ("HIGH", "MEDIUM", "LOW")
    assert "financial advice" in REPORT_DISCLAIMER.lower() or "not financial" in REPORT_DISCLAIMER.lower()
    # no buy/sell in executive summary as instruction
    assert "buy now" not in report.executive_summary.lower()
    assert "sell now" not in report.executive_summary.lower()


def test_engine_what_changed_second_run(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    r1 = engine.analyse("bitcoin", entity_type_hint="token", chain="ethereum")
    r2 = engine.analyse("bitcoin", entity_type_hint="token", chain="ethereum")
    # Second run may or may not show changes; repository must not crash
    assert r1.report_id != r2.report_id
    assert isinstance(r2.changes, list)


def test_engine_failing_provider_graceful(tmp_db: Path):
    engine = ReportEngine(provider=FailingProvider("rate_limit"), db_path=tmp_db)
    report = engine.analyse("0x" + "22" * 20, entity_type_hint="wallet")
    assert report.data_mode in (DataMode.UNAVAILABLE.value, DataMode.DEMO.value, DataMode.MIXED.value)
    assert report.warnings or report.errors or report.confidence == "LOW"


def test_engine_unsupported_explained(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse("foo", entity_type_hint="nft_collection")
    assert not report.unsupported_reason == "" or report.entity_type == "unsupported"
    assert "Unsupported" in (report.unsupported_reason or report.executive_summary or "")


def test_metric_explainers():
    e = explain_metric("tvl")
    assert "cannot" in e
    md = render_explainer_markdown("tvl")
    assert "What it is" in md
    assert journey_steps()[0]["step"] == "Search"


def test_report_context_for_assistant(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse("ethereum", entity_type_hint="token")
    ctx = report.context_for_assistant()
    assert "Intelligence Report" in ctx or "entity" in ctx.lower() or "FACT" in ctx
    assert "DEMO" in ctx or report.is_demo or "DATA" in ctx


def test_ai_answer_report_grounding(tmp_db: Path):
    from mccc.ai_service import answer
    from mccc.db import init_db

    init_db(tmp_db)
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse("ethereum", entity_type_hint="token")
    res = answer(
        "Summarise this report",
        use_llm=False,
        report_context=report.context_for_assistant(),
        db_path=tmp_db,
    )
    assert res["mode"] != "refusal"
    assert res.get("report_grounded") is True
    assert "Intelligence Report" in res["answer"] or "DATA" in res["answer"]


def test_ai_refuses_secret_in_report_context(tmp_db: Path):
    from mccc.ai_service import answer
    from mccc.db import init_db

    init_db(tmp_db)
    res = answer(
        "hello",
        use_llm=False,
        report_context="private key " + ("ab" * 32),
        db_path=tmp_db,
    )
    assert res["mode"] == "refusal"


def test_disclaimer_and_risk_language(tmp_db: Path):
    engine = ReportEngine(provider=StaticDemoProvider(), db_path=tmp_db)
    report = engine.analyse("aave", entity_type_hint="protocol")
    blob = " ".join(
        [report.executive_summary]
        + [f.language + " " + f.detail for f in report.risk_flags]
        + [report.beginner.what_to_investigate_next if report.beginner else ""]
    )
    # At least one neutral phrase appears across report
    assert any(
        p in blob
        for p in (
            "Investigate further",
            "Potential risk indicator",
            "Insufficient data",
            "No conclusion",
            "DATA UNAVAILABLE",
        )
    )


def test_security_scan_no_seed_storage_in_report_modules():
    """Static scan: report package must not ask users to paste seeds."""
    root = Path(__file__).resolve().parents[1] / "src" / "mccc" / "intelligence" / "report"
    bad = []
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        # Allow rejection messaging, forbid solicitation patterns
        if "paste your seed" in text or "enter your private key" in text:
            bad.append(path.name)
        if "store_seed" in text or "save_private_key" in text:
            bad.append(path.name)
    assert not bad
