"""Intelligence Report engine — Providers → Normalisation → Analytics → Report."""
from __future__ import annotations

import hashlib
import uuid
from typing import Any, Optional

from mccc.db import utc_now
from mccc.intelligence.report import analytics as A
from mccc.intelligence.report import normalize as N
from mccc.intelligence.report.education import explain_metric
from mccc.intelligence.report.providers import MCCCReportProvider, ReportDataProvider
from mccc.intelligence.report.repository import ReportRepository
from mccc.intelligence.report.schema import (
    REPORT_DISCLAIMER,
    DataMode,
    DataQuality,
    EntityType,
    IntelligenceReport,
    SourceRef,
)
from mccc.intelligence.report.validators import validate_report_query


def _qid(entity_type: str, normalized: str, chain: str) -> str:
    raw = f"{entity_type}|{normalized.lower()}|{chain.lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _confidence(reasons_pos: list[str], reasons_neg: list[str], *, live: bool, demo: bool, partial: bool) -> tuple[str, list[str]]:
    reasons = list(reasons_pos) + list(reasons_neg)
    if reasons_neg and not reasons_pos:
        return DataQuality.LOW.value, reasons or ["Insufficient reliable fields"]
    if live and not demo and not partial and not reasons_neg:
        return DataQuality.HIGH.value, reasons or ["Live provider data with complete core fields"]
    if live and partial:
        return DataQuality.MEDIUM.value, reasons or ["Live provider responded but some fields missing"]
    if demo and not live:
        return DataQuality.LOW.value, reasons or ["DEMO/SYNTHETIC or fallback data only"]
    if partial or reasons_neg:
        return DataQuality.MEDIUM.value, reasons or ["Partial research data"]
    return DataQuality.MEDIUM.value, reasons or ["Mixed local research signals"]


class ReportEngine:
    """Build 10-section Intelligence Reports for supported entities."""

    def __init__(
        self,
        provider: Optional[ReportDataProvider] = None,
        repository: Optional[ReportRepository] = None,
        db_path=None,
    ) -> None:
        self.db_path = db_path
        self.provider = provider or MCCCReportProvider(db_path=db_path)
        self.repo = repository or ReportRepository(db_path=db_path)
        self.repo.ensure_schema()

    def analyse(
        self,
        query: str,
        *,
        entity_type_hint: Optional[str] = None,
        chain: str = "ethereum",
        persist: bool = True,
    ) -> IntelligenceReport:
        v = validate_report_query(query, entity_type_hint=entity_type_hint, chain=chain)
        created = utc_now()
        report_id = str(uuid.uuid4())

        if not v.ok:
            return IntelligenceReport(
                report_id=report_id,
                entity_type=v.entity_type or EntityType.UNSUPPORTED.value,
                query=v.query,
                display_name=v.query or "(empty)",
                chain=v.chain,
                data_mode=DataMode.UNAVAILABLE.value,
                confidence=DataQuality.LOW.value,
                confidence_reasons=[v.error or "Invalid input"],
                executive_summary=v.error or "Could not analyse this input.",
                what_is_this_plain="Input was rejected or unsupported.",
                what_is_this_advanced=v.error,
                unsupported_reason=v.error,
                errors=[v.error] if v.error else [],
                warnings=list(v.warnings or []),
                created_at=created,
                beginner=A.beginner_summary(
                    entity_type=v.entity_type or "unsupported",
                    display_name=v.query or "(empty)",
                    data_mode=DataMode.UNAVAILABLE.value,
                    confidence=DataQuality.LOW.value,
                    risk_flags=[],
                ),
                sources=[
                    SourceRef(
                        title="MCCC security / validation",
                        source_type="internal",
                        note="Public address only; secrets rejected.",
                    )
                ],
            )

        entity = v.entity_type
        q = v.normalized
        ch = v.chain
        warnings = list(v.warnings or [])

        # Fetch + normalise by entity
        if entity == EntityType.WALLET.value:
            raw = self.provider.fetch_wallet(q, chain=ch)
            norm = N.normalize_wallet(raw)
            analysed = A.analyze_wallet(norm)
            display = q
        elif entity == EntityType.CONTRACT.value:
            raw = self.provider.fetch_wallet(q, chain=ch)
            norm = N.normalize_wallet(raw)
            analysed = A.analyze_contract(norm)
            display = q
        elif entity == EntityType.TOKEN.value:
            raw = self.provider.fetch_token(q)
            norm = N.normalize_token(raw)
            analysed = A.analyze_token(norm)
            display = str(norm.get("symbol") or norm.get("name") or q)
        elif entity == EntityType.PROTOCOL.value:
            raw = self.provider.fetch_protocol(q)
            norm = N.normalize_protocol(raw)
            analysed = A.analyze_protocol(norm)
            proj = norm.get("project") or {}
            display = str((proj or {}).get("name") or q)
        elif entity == EntityType.RWA.value:
            raw = self.provider.fetch_rwa(q)
            norm = N.normalize_rwa(raw)
            analysed = A.analyze_rwa(norm)
            profile = norm.get("profile") or {}
            display = str(profile.get("name") or q)
        else:  # project default
            raw = self.provider.fetch_project(q)
            norm = N.normalize_project(raw)
            analysed = A.analyze_project(norm)
            proj = norm.get("project") or {}
            display = str((proj or {}).get("name") or q)
            entity = EntityType.PROJECT.value

        # Optional intel enrichment (non-fatal)
        intel = self.provider.fetch_intel_events(q, limit=8)
        intel_events = (intel.data or {}).get("events") or []

        metrics = list(analysed.get("metrics") or [])
        risk_flags = list(analysed.get("risk_flags") or [])
        wallet_intel = dict(analysed.get("wallet_intelligence") or {})
        token_intel = dict(analysed.get("token_intelligence") or {})

        is_demo = bool(getattr(raw, "is_demo", False) or norm.get("is_demo"))
        is_live = bool(getattr(raw, "is_live", False) or norm.get("is_live"))
        partial = bool(getattr(raw, "partial", False) or norm.get("partial"))
        if getattr(raw, "rate_limited", False):
            warnings.append("Provider rate-limited — showing DATA UNAVAILABLE / partial research state.")
        if getattr(raw, "timed_out", False):
            warnings.append("Provider timed out — graceful degradation applied.")
        if raw.error:
            warnings.append(raw.error)

        if is_live and is_demo:
            data_mode = DataMode.MIXED.value
        elif is_live:
            data_mode = DataMode.LIVE.value
        elif is_demo:
            data_mode = DataMode.DEMO.value
        elif not raw.ok:
            data_mode = DataMode.UNAVAILABLE.value
        else:
            data_mode = DataMode.DEMO.value  # local research without live chain = not claimed live

        pos, neg = [], []
        if is_live:
            pos.append("At least one live provider field present")
        if is_demo:
            neg.append("DEMO/SYNTHETIC or fallback rows included")
        if partial or not raw.ok:
            neg.append("Partial or failed provider response")
        if intel_events:
            pos.append(f"{len(intel_events)} related intelligence event(s) found locally")
        conf, conf_reasons = _confidence(pos, neg, live=is_live, demo=is_demo, partial=partial or not raw.ok)

        # What changed?
        prev = self.repo.previous_observation(entity_type=entity, query_key=q, chain=ch)
        snapshot = {
            "entity_type": entity,
            "query": q,
            "chain": ch,
            "display_name": display,
            "data_mode": data_mode,
            "confidence": conf,
            "metric_values": {m.key: m.value for m in metrics},
            "is_demo": is_demo,
            "normalized_at": norm.get("normalized_at") or created,
        }
        changes = A.detect_activity_change(prev, snapshot)

        # Narratives
        exec_summary = self._executive_summary(
            entity=entity,
            display=display,
            data_mode=data_mode,
            confidence=conf,
            norm=norm,
            analysed=analysed,
            is_demo=is_demo,
        )
        plain, advanced = self._what_is_this(entity, display, norm, analysed, chain=ch)

        sources = self._sources(entity, raw_source=str(getattr(raw, "source", "") or ""), norm=norm, intel_events=intel_events)
        beginner = A.beginner_summary(
            entity_type=entity,
            display_name=display,
            data_mode=data_mode,
            confidence=conf,
            risk_flags=risk_flags,
        )

        report = IntelligenceReport(
            report_id=report_id,
            entity_type=entity,
            query=v.query,
            display_name=display,
            chain=ch,
            data_mode=data_mode,
            confidence=conf,
            confidence_reasons=conf_reasons,
            executive_summary=exec_summary,
            what_is_this_plain=plain,
            what_is_this_advanced=advanced,
            on_chain_metrics=metrics,
            wallet_intelligence=wallet_intel,
            token_intelligence=token_intel,
            risk_flags=risk_flags,
            changes=changes,
            beginner=beginner,
            sources=sources,
            errors=[raw.error] if (raw.error and not raw.ok) else [],
            warnings=warnings,
            is_demo=is_demo,
            created_at=created,
            raw_snapshot={
                "norm": {k: v for k, v in norm.items() if k != "balances"},
                "intel_event_ids": [e.get("id") for e in intel_events[:8] if isinstance(e, dict)],
                "provider": getattr(self.provider, "name", "unknown"),
                "metric_explainers": {m.key: explain_metric(m.key) for m in metrics[:8]},
                "query_fingerprint": _qid(entity, q, ch),
            },
        )

        if persist:
            self.repo.save_observation(
                report_id=report_id,
                entity_type=entity,
                query_key=q,
                chain=ch,
                snapshot=snapshot,
                confidence=conf,
                data_mode=data_mode,
                is_demo=is_demo,
            )
        return report

    def _executive_summary(
        self,
        *,
        entity: str,
        display: str,
        data_mode: str,
        confidence: str,
        norm: dict[str, Any],
        analysed: dict[str, Any],
        is_demo: bool,
    ) -> str:
        demo_bit = " Includes DEMO/SYNTHETIC labelled data." if is_demo else ""
        base = (
            f"Research summary for **{display}** ({entity}). "
            f"Data mode **{data_mode}**, confidence **{confidence}**.{demo_bit} "
            "This report helps answer what the entity appears to be doing in public data — "
            "not what to buy or sell."
        )
        if entity in (EntityType.WALLET.value, EntityType.CONTRACT.value):
            n = norm.get("balance_count") or 0
            status = "ok" if norm.get("provider_ok") else "DATA UNAVAILABLE"
            return base + f" Public balance lookup status: {status}; observed token rows: {n}."
        if entity == EntityType.TOKEN.value:
            px = norm.get("price")
            tag = "LIVE" if norm.get("is_live") else "DEMO/FALLBACK"
            return base + f" Provider price ({tag}): {px if px is not None else 'DATA UNAVAILABLE'}."
        if entity == EntityType.PROTOCOL.value:
            return base + " TVL is not invented; see metrics for DATA UNAVAILABLE when unverified."
        if entity == EntityType.RWA.value:
            return base + " RWA disclosure diligence still required — see risk flags."
        proj = analysed.get("project") or norm.get("project")
        if proj:
            return base + f" Local tracker stage: {proj.get('stage') or proj.get('status') or 'unknown'}."
        return base + " Insufficient local project match — Investigate further with primary sources."

    def _what_is_this(
        self,
        entity: str,
        display: str,
        norm: dict[str, Any],
        analysed: dict[str, Any],
        *,
        chain: str,
    ) -> tuple[str, str]:
        plain = f"**{display}** is classified as a `{entity}` for this analysis (chain hint: {chain})."
        advanced_parts = [
            f"entity_type={entity}",
            f"chain={chain}",
            f"provider_source={norm.get('source')}",
            f"provider_ok={norm.get('provider_ok')}",
            f"is_demo={norm.get('is_demo')}",
            f"is_live={norm.get('is_live')}",
            f"partial={norm.get('partial')}",
        ]
        if entity == EntityType.TOKEN.value:
            plain += f" Symbol/name: {norm.get('symbol') or 'Unknown'} / {norm.get('name') or 'Unknown'}."
            advanced_parts.append(f"token_id={norm.get('token_id')}")
            advanced_parts.append(f"verification={norm.get('verification')}")
        if entity in (EntityType.WALLET.value, EntityType.CONTRACT.value):
            plain += (
                " Public address trail may include transactions, token movements, and protocol interactions "
                "when a reliable provider supplies them. MCCC does not need control of your wallet to analyse "
                "public blockchain activity."
            )
            advanced_parts.append(f"address={norm.get('address')}")
        if entity == EntityType.RWA.value:
            profile = norm.get("profile") or {}
            plain += f" RWA category: {profile.get('category') or 'Unknown / Not disclosed'}."
        if entity == EntityType.PROTOCOL.value:
            plain += " Protocol view combines local research + intelligence events; TVL only when verified."
        if entity == EntityType.PROJECT.value:
            proj = norm.get("project")
            if proj:
                plain += f" Matched local project notes/stage for diligence tracking."
            else:
                plain += " No strong local project match — treat as a search starting point."
        return plain, " · ".join(advanced_parts)

    def _sources(self, entity: str, *, raw_source: str, norm: dict[str, Any], intel_events: list) -> list[SourceRef]:
        out = [
            SourceRef(title="Report disclaimer", note=REPORT_DISCLAIMER[:180], source_type="policy"),
        ]
        if raw_source:
            out.append(SourceRef(title="Primary provider", note=raw_source, source_type="provider"))
        if entity in (EntityType.WALLET.value, EntityType.CONTRACT.value):
            out.append(
                SourceRef(
                    title="Public explorer / RPC (when configured)",
                    note="Etherscan API key optional; Cloudflare public RPC soft-fail; DEMO addresses use DEMO table.",
                    source_type="chain",
                )
            )
        if entity == EntityType.TOKEN.value:
            out.append(
                SourceRef(
                    title="market_provider / CoinGecko",
                    note=str(norm.get("source") or raw_source),
                    source_type="market",
                )
            )
        if entity == EntityType.RWA.value:
            out.append(SourceRef(title="RWA Intelligence profiles", source_type="rwa", note="Local RWAService"))
        out.append(
            SourceRef(
                title="Intelligence events (local)",
                note=f"{len(intel_events)} match(es) in local repository",
                source_type="intelligence",
            )
        )
        # Real URLs only from intel events
        for ev in intel_events[:5]:
            url = (ev or {}).get("source_url") or ""
            if url.startswith("http"):
                out.append(
                    SourceRef(
                        title=(ev.get("title") or "Intelligence source")[:80],
                        url=url,
                        source_type="intelligence_event",
                        note="From stored intelligence event — verify independently.",
                    )
                )
        return out
