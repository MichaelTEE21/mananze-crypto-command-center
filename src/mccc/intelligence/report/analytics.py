"""Analytics helpers for Intelligence Reports.

Naming matches codebase plan: analyze_wallet/token/protocol, detect_activity_change,
concentration, summarize_transactions, risk indicators, beginner summary.
Never invents transactions or live stats.
"""
from __future__ import annotations

from typing import Any, Optional

from mccc.intelligence.report.schema import (
    BeginnerBlock,
    ChangeObservation,
    Metric,
    Provenance,
    RiskFlag,
    VerificationLevel,
)


def summarize_transactions(tx_rows: Optional[list[dict[str, Any]]]) -> dict[str, Any]:
    """Summarise public txs only when rows are provided by a provider — never invent."""
    if not tx_rows:
        return {
            "count": None,
            "status": "DATA UNAVAILABLE",
            "note": "No reliable transaction feed in this build — Insufficient data.",
            "rows": [],
        }
    return {
        "count": len(tx_rows),
        "status": "observed",
        "note": "Counts reflect provider rows only.",
        "rows": tx_rows[:50],
    }


def concentration(balances: list[dict[str, Any]]) -> dict[str, Any]:
    """Holding concentration from observed balances (amount or usd when present)."""
    if not balances:
        return {
            "score": None,
            "top_share": None,
            "status": "Insufficient data",
            "note": "No balances to assess concentration.",
        }
    weights = []
    for b in balances:
        w = b.get("usd_value")
        if w is None:
            w = b.get("amount")
        try:
            weights.append(max(0.0, float(w or 0)))
        except (TypeError, ValueError):
            weights.append(0.0)
    total = sum(weights)
    if total <= 0:
        return {
            "score": None,
            "top_share": None,
            "status": "Insufficient data",
            "note": "Balance weights unavailable or zero.",
        }
    top = max(weights) / total
    # Herfindahl-ish
    hhi = sum((w / total) ** 2 for w in weights)
    return {
        "score": round(hhi, 4),
        "top_share": round(top, 4),
        "status": "observed",
        "note": "Potential risk indicator only — No conclusion on intent or safety.",
    }


def detect_activity_change(
    previous: Optional[dict[str, Any]],
    current: dict[str, Any],
) -> list[ChangeObservation]:
    """Compare prior observation snapshot to current — invent no causes."""
    if not previous:
        return []
    changes: list[ChangeObservation] = []
    keys = sorted(set(previous.keys()) | set(current.keys()))
    for key in keys:
        if key in ("normalized_at", "created_at", "report_id", "raw_snapshot"):
            continue
        pv = previous.get(key)
        cv = current.get(key)
        if pv != cv:
            # Only shallow scalar / small changes
            if isinstance(pv, (dict, list)) or isinstance(cv, (dict, list)):
                if str(pv) != str(cv):
                    changes.append(
                        ChangeObservation(
                            field=key,
                            previous=_short(pv),
                            current=_short(cv),
                            observed_at_previous=str(previous.get("normalized_at") or previous.get("created_at") or ""),
                            observed_at_current=str(current.get("normalized_at") or current.get("created_at") or ""),
                        )
                    )
            else:
                changes.append(
                    ChangeObservation(
                        field=key,
                        previous=pv,
                        current=cv,
                        observed_at_previous=str(previous.get("normalized_at") or previous.get("created_at") or ""),
                        observed_at_current=str(current.get("normalized_at") or current.get("created_at") or ""),
                    )
                )
    return changes[:20]


def _short(val: Any, n: int = 120) -> Any:
    s = str(val)
    return s if len(s) <= n else s[: n - 3] + "..."


def risk_indicators_for_wallet(norm: dict[str, Any]) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if norm.get("rate_limited"):
        flags.append(
            RiskFlag(
                code="rate_limited",
                title="Provider rate limit",
                detail="Balance/activity lookup hit a rate limit — Investigate further when capacity returns.",
                language="Investigate further",
                severity="warn",
            )
        )
    if norm.get("timed_out"):
        flags.append(
            RiskFlag(
                code="timeout",
                title="Provider timeout",
                detail="Public lookup timed out — Insufficient data for this refresh.",
                language="Insufficient data",
                severity="warn",
            )
        )
    if not norm.get("provider_ok") or norm.get("partial"):
        flags.append(
            RiskFlag(
                code="partial_wallet_data",
                title="Incomplete public wallet data",
                detail="Some or all on-chain fields are unavailable. No conclusion on full activity.",
                language="Insufficient data",
                severity="info",
            )
        )
    conc = concentration(norm.get("balances") or [])
    if conc.get("top_share") is not None and conc["top_share"] >= 0.9:
        flags.append(
            RiskFlag(
                code="high_concentration",
                title="High observed concentration",
                detail=(
                    f"Top asset share ≈ {conc['top_share']:.0%} of observed weights. "
                    "Potential risk indicator for diversification research — No conclusion."
                ),
                language="Potential risk indicator",
                severity="investigate",
            )
        )
    flags.append(
        RiskFlag(
            code="identity_caution",
            title="No ownership identity claim",
            detail=(
                "This address interacted with public networks as observed — "
                "MCCC will not claim this wallet belongs to a named person/entity without "
                "a verified authoritative public source."
            ),
            language="No conclusion",
            severity="info",
        )
    )
    return flags


def risk_indicators_generic(
    *,
    missing_critical: bool = False,
    is_demo: bool = False,
    extra: Optional[list[RiskFlag]] = None,
) -> list[RiskFlag]:
    flags: list[RiskFlag] = list(extra or [])
    if missing_critical:
        flags.append(
            RiskFlag(
                code="missing_critical",
                title="Critical fields missing",
                detail="Key verified fields are missing — Insufficient data for strong conclusions.",
                language="Insufficient data",
                severity="warn",
            )
        )
    if is_demo:
        flags.append(
            RiskFlag(
                code="demo_data",
                title="DEMO / SYNTHETIC data present",
                detail="Report includes labelled DEMO/SYNTHETIC rows — never treat as live markets or live chain state.",
                language="Investigate further",
                severity="info",
            )
        )
    return flags


def analyze_wallet(norm: dict[str, Any]) -> dict[str, Any]:
    tx_summary = summarize_transactions(norm.get("transactions"))
    conc = concentration(norm.get("balances") or [])
    metrics: list[Metric] = []
    ts = norm.get("normalized_at") or ""
    chain = norm.get("chain") or "unknown"
    for b in norm.get("balances") or []:
        live = bool(b.get("is_live"))
        metrics.append(
            Metric(
                key=f"balance_{(b.get('token') or 'unk').lower()}",
                label=f"{b.get('token')} balance",
                value=b.get("amount"),
                unit=str(b.get("token") or ""),
                provenance=Provenance(
                    source=str(b.get("source") or norm.get("source") or "unknown"),
                    timestamp=ts,
                    chain=chain,
                    definition="Public native/token balance when provider responds.",
                    is_live=live,
                    verification=VerificationLevel.VERIFIED.value if live else VerificationLevel.ESTIMATED.value,
                ),
            )
        )
    if not metrics:
        metrics.append(
            Metric(
                key="balance",
                label="Public balance",
                value=None,
                unavailable_reason=norm.get("provider_error") or "DATA UNAVAILABLE",
                provenance=Provenance(
                    source=norm.get("source") or "wallet_provider",
                    timestamp=ts,
                    chain=chain,
                    definition="Public balance lookup",
                    is_live=False,
                ),
            )
        )
    metrics.append(
        Metric(
            key="tx_count",
            label="Observed transaction count",
            value=tx_summary.get("count"),
            unavailable_reason="" if tx_summary.get("count") is not None else tx_summary.get("note", "DATA UNAVAILABLE"),
            provenance=Provenance(
                source="transaction_feed",
                timestamp=ts,
                chain=chain,
                definition="Count of provider-supplied public transactions in window.",
                is_live=False,
            ),
        )
    )
    metrics.append(
        Metric(
            key="concentration",
            label="Concentration (HHI-like)",
            value=conc.get("score"),
            unavailable_reason="" if conc.get("score") is not None else conc.get("note", "Insufficient data"),
            provenance=Provenance(
                source="derived:concentration",
                timestamp=ts,
                chain=chain,
                definition=METRIC_DEF_CONCENTRATION,
                is_live=False,
                verification=VerificationLevel.ESTIMATED.value,
            ),
        )
    )
    return {
        "metrics": metrics,
        "tx_summary": tx_summary,
        "concentration": conc,
        "risk_flags": risk_indicators_for_wallet(norm),
        "wallet_intelligence": {
            "address": norm.get("address"),
            "chain": chain,
            "interaction_note": (
                "This address interacted with public chain infrastructure as far as available data shows. "
                "No ownership identity is asserted."
            ),
            "balance_count": norm.get("balance_count"),
            "total_known_usd": norm.get("total_known_usd"),
            "data_status": "ok" if norm.get("provider_ok") else "DATA UNAVAILABLE",
        },
    }


METRIC_DEF_CONCENTRATION = (
    "Derived share concentration from observed balances; Potential risk indicator only."
)


def analyze_token(norm: dict[str, Any]) -> dict[str, Any]:
    ts = norm.get("normalized_at") or ""
    live = bool(norm.get("is_live"))
    verification = norm.get("verification") or (
        VerificationLevel.VERIFIED.value if live else VerificationLevel.ESTIMATED.value
    )
    metrics = [
        Metric(
            key="price",
            label="Price (USD)",
            value=norm.get("price"),
            unit="USD",
            unavailable_reason="" if norm.get("price") is not None else (norm.get("provider_error") or "DATA UNAVAILABLE"),
            provenance=Provenance(
                source=str(norm.get("source") or "market_provider"),
                timestamp=ts,
                chain="market",
                definition="Spot price from market_provider when reachable.",
                is_live=live,
                verification=verification,
            ),
        ),
        Metric(
            key="market_cap",
            label="Market cap",
            value=norm.get("market_cap"),
            unit="USD",
            unavailable_reason="" if norm.get("market_cap") is not None else "DATA UNAVAILABLE or not provided",
            provenance=Provenance(
                source=str(norm.get("source") or "market_provider"),
                timestamp=ts,
                chain="market",
                definition="Circulating mcap from provider — not fundamental value.",
                is_live=live,
                verification=verification,
            ),
        ),
    ]
    token_intel = {
        "token_id": norm.get("token_id"),
        "symbol": norm.get("symbol"),
        "name": norm.get("name"),
        "verification": verification,
        "verification_note": (
            "verified = live provider quote; estimated = DEMO/fallback; "
            "user_provided = not used unless explicitly entered elsewhere."
        ),
        "change_24h": norm.get("change_24h"),
        "is_live": live,
        "is_demo": bool(norm.get("is_demo")),
    }
    flags = risk_indicators_generic(
        missing_critical=norm.get("price") is None,
        is_demo=bool(norm.get("is_demo")),
    )
    return {"metrics": metrics, "token_intelligence": token_intel, "risk_flags": flags}


def analyze_protocol(norm: dict[str, Any]) -> dict[str, Any]:
    ts = norm.get("normalized_at") or ""
    metrics = [
        Metric(
            key="tvl",
            label="TVL",
            value=norm.get("tvl"),
            unit="USD",
            unavailable_reason=norm.get("tvl_note") or "DATA UNAVAILABLE",
            provenance=Provenance(
                source=str(norm.get("source") or "protocol_composite"),
                timestamp=ts,
                chain="multi",
                definition="Total Value Locked when a verified provider supplies it — never invented.",
                is_live=False,
                verification=VerificationLevel.UNKNOWN.value,
            ),
        ),
        Metric(
            key="intel_event_count",
            label="Related intelligence events",
            value=len(norm.get("events") or []),
            provenance=Provenance(
                source="intelligence_repository",
                timestamp=ts,
                chain="research",
                definition="Count of locally stored intelligence events matching query.",
                is_live=False,
                verification=VerificationLevel.ESTIMATED.value,
            ),
        ),
    ]
    flags = risk_indicators_generic(
        missing_critical=norm.get("tvl") is None and not norm.get("project") and not norm.get("events"),
        is_demo=bool(norm.get("is_demo")),
        extra=[
            RiskFlag(
                code="tvl_unavailable",
                title="TVL not verified in this build",
                detail=str(norm.get("tvl_note") or "DATA UNAVAILABLE — will not invent TVL."),
                language="Insufficient data",
                severity="info",
            )
        ],
    )
    return {
        "metrics": metrics,
        "wallet_intelligence": {},
        "token_intelligence": {},
        "risk_flags": flags,
        "project": norm.get("project"),
        "events": norm.get("events") or [],
    }


def analyze_project(norm: dict[str, Any]) -> dict[str, Any]:
    proj = norm.get("project")
    flags = risk_indicators_generic(
        missing_critical=proj is None,
        is_demo=bool(norm.get("is_demo")),
    )
    metrics: list[Metric] = []
    if proj:
        metrics.append(
            Metric(
                key="local_stage",
                label="Local tracker stage",
                value=proj.get("stage") or proj.get("status") or "unknown",
                provenance=Provenance(
                    source="local_projects_db",
                    timestamp=norm.get("normalized_at") or "",
                    chain=str(proj.get("chain") or "unknown"),
                    definition="User/local research stage — not an on-chain fact.",
                    is_live=False,
                    verification=VerificationLevel.USER_PROVIDED.value,
                ),
            )
        )
    return {
        "metrics": metrics,
        "project": proj,
        "hits": norm.get("hits") or [],
        "risk_flags": flags,
        "wallet_intelligence": {},
        "token_intelligence": {},
    }


def analyze_contract(norm_wallet: dict[str, Any], *, label: str = "contract") -> dict[str, Any]:
    """Contracts share address shape with wallets — reuse wallet analytics with caution notes."""
    base = analyze_wallet(norm_wallet)
    base["risk_flags"] = list(base.get("risk_flags") or []) + [
        RiskFlag(
            code="contract_wallet_ambiguity",
            title="Contract vs EOA ambiguity",
            detail=(
                "EVM contract addresses share the 0x format with wallets. "
                "Treat bytecode/verified-source checks as Investigate further — "
                "Insufficient data in this report to classify contract type automatically."
            ),
            language="Investigate further",
            severity="investigate",
        )
    ]
    wi = dict(base.get("wallet_intelligence") or {})
    wi["entity_hint"] = label
    wi["interaction_note"] = (
        "This address interacted with the chain as a public 0x identifier. "
        "Contract classification requires explorer verification — No conclusion here."
    )
    base["wallet_intelligence"] = wi
    return base


def analyze_rwa(norm: dict[str, Any]) -> dict[str, Any]:
    profile = norm.get("profile") or {}
    flags = risk_indicators_generic(
        missing_critical=not profile,
        is_demo=bool(norm.get("is_demo") or profile.get("is_demo")),
        extra=[
            RiskFlag(
                code="rwa_disclosure",
                title="RWA disclosure diligence",
                detail=(
                    "Investigate further: custody, redemption, attestation, and jurisdictional disclosures. "
                    "Missing fields mean Insufficient data — No conclusion."
                ),
                language="Investigate further",
                severity="investigate",
            )
        ],
    )
    metrics: list[Metric] = []
    if profile:
        metrics.append(
            Metric(
                key="rwa_category",
                label="RWA category",
                value=profile.get("category") or profile.get("subcategory") or "unknown",
                provenance=Provenance(
                    source="rwa_service",
                    timestamp=norm.get("normalized_at") or "",
                    chain=str(profile.get("chain") or "unknown"),
                    definition="Taxonomy category from RWA Intelligence profiles.",
                    is_live=False,
                    verification=VerificationLevel.ESTIMATED.value
                    if profile.get("is_demo")
                    else VerificationLevel.VERIFIED.value,
                ),
            )
        )
        # Asset value if present — honour existing labelling
        av = profile.get("asset_value") or profile.get("reported_value") or profile.get("value_estimate")
        metrics.append(
            Metric(
                key="rwa_value",
                label="Asset value field",
                value=av,
                unavailable_reason="" if av is not None else "Unknown / Not disclosed / Unconfirmed",
                provenance=Provenance(
                    source="rwa_service",
                    timestamp=str(profile.get("updated_at") or norm.get("normalized_at") or ""),
                    chain=str(profile.get("chain") or "unknown"),
                    definition="Verified reported vs calculated estimate (not TVL) per RWA Phase 1 rules.",
                    is_live=False,
                    verification=VerificationLevel.ESTIMATED.value,
                ),
            )
        )
    return {
        "metrics": metrics,
        "profile": profile,
        "hits": norm.get("hits") or [],
        "risk_flags": flags,
        "wallet_intelligence": {},
        "token_intelligence": {},
    }


def beginner_summary(
    *,
    entity_type: str,
    display_name: str,
    data_mode: str,
    confidence: str,
    risk_flags: list[RiskFlag],
) -> BeginnerBlock:
    mean = (
        f"{display_name} is being analysed as a **{entity_type}** using public research data. "
        f"Data mode: {data_mode}. Confidence: {confidence}."
    )
    care = (
        "It helps answer “What is this entity actually doing / how is it represented on-chain or in local research?” "
        "— not what to buy or sell."
    )
    next_steps = [
        "Open primary sources listed in the Sources section",
        "Compare LIVE vs DEMO labels before trusting any number",
        "If this is a wallet/contract, verify the address on a reputable block explorer",
    ]
    if any(r.language == "Investigate further" for r in risk_flags):
        next_steps.append("Review items marked Investigate further / Potential risk indicator")
    if data_mode in ("DATA_UNAVAILABLE", "DEMO"):
        next_steps.append("Retry when providers are reachable, or use labelled DEMO only for practice")
    return BeginnerBlock(
        what_does_this_mean=mean,
        why_should_i_care=care,
        what_to_investigate_next=" · ".join(next_steps),
    )
