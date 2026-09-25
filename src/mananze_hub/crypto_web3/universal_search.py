"""Universal search — entity detection, chips, ANALYSE routing helpers.

Builds on intelligence/report validators + existing search_all. Pure helpers (no Streamlit).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from mccc.intelligence.report.validators import (
    detect_entity_type,
    strip_prefix,
    validate_report_query,
)
from mccc.search import search_all

ENTITY_CHIPS = (
    "Token",
    "Project",
    "Contract",
    "Airdrop",
    "Protocol",
    "Wallet",
)

# Map detected entity_type → chip label
_ENTITY_TO_CHIP = {
    "token": "Token",
    "project": "Project",
    "contract": "Contract",
    "protocol": "Protocol",
    "wallet": "Wallet",
    "rwa": "Project",  # surface as research entity chip; RWA vertical is separate
    "airdrop": "Airdrop",
}

_CHIP_TO_ENTITY = {v.lower(): k for k, v in _ENTITY_TO_CHIP.items()}
_CHIP_TO_ENTITY["airdrop"] = "airdrop"


@dataclass
class DetectedEntity:
    query: str
    normalized: str
    entity_type: str
    chip: str
    ok: bool
    error: str = ""
    rejected_secret: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def chip_for_entity(entity_type: str) -> str:
    return _ENTITY_TO_CHIP.get((entity_type or "").lower(), "Project")


def detect_search_entity(query: str, hint: Optional[str] = None) -> DetectedEntity:
    """Detect entity for universal search / homepage ANALYSE.

    Reuses report validation so secrets are rejected consistently.
    """
    raw = (query or "").strip()
    # Dollar-ticker → token (user-friendly, no jargon required)
    hint_norm = (hint or "").strip().lower() or None
    q_for_detect = raw
    if raw.startswith("$") and len(raw) > 1:
        q_for_detect = raw[1:].strip()
        hint_norm = hint_norm or "token"

    # Airdrop-ish names without forcing jargon
    lower = raw.lower()
    if hint_norm is None and ("airdrop" in lower or lower.startswith("airdrop:")):
        hint_norm = "airdrop" if "airdrop" in ("airdrop",) else hint_norm

    if hint_norm == "airdrop":
        # Airdrop is a search category, not always a report entity — still allow ANALYSE as project
        from mccc.security import SensitiveCredentialError, reject_sensitive_credential

        try:
            reject_sensitive_credential(raw, field="search.query")
        except SensitiveCredentialError as exc:
            return DetectedEntity(
                query=raw,
                normalized="",
                entity_type="unsupported",
                chip="Airdrop",
                ok=False,
                error=str(exc),
                rejected_secret=True,
            )
        body = strip_prefix(raw.replace("airdrop:", " ").strip())
        return DetectedEntity(
            query=raw,
            normalized=body or raw,
            entity_type="airdrop",
            chip="Airdrop",
            ok=bool(body or raw),
            error="" if (body or raw) else "Enter an airdrop or project name.",
        )

    v = validate_report_query(q_for_detect, entity_type_hint=hint_norm)
    chip = chip_for_entity(v.entity_type)
    return DetectedEntity(
        query=raw,
        normalized=v.normalized,
        entity_type=v.entity_type,
        chip=chip,
        ok=v.ok,
        error=v.error,
        rejected_secret=v.rejected_secret,
        warnings=list(v.warnings or []),
    )


def analyse_session_payload(detected: DetectedEntity) -> dict[str, str]:
    """Payload to stash in session_state before switching to Intelligence Center."""
    return {
        "intel_report_q": detected.normalized or detected.query,
        "mccc_analyse_entity_hint": detected.entity_type
        if detected.entity_type not in ("airdrop", "unknown", "unsupported")
        else "auto",
        "mccc_search_q": detected.query,
    }


def unified_search_results(
    query: str,
    *,
    db_path=None,
    limit_per: int = 15,
) -> dict[str, Any]:
    """Run category search + attach detected entity metadata and typed hit chips."""
    detected = detect_search_entity(query)
    cats = search_all(query, db_path=db_path, limit_per=limit_per) if detected.ok or query.strip() else {}
    typed_hits: list[dict[str, Any]] = []

    def _add(chip: str, title: str, subtitle: str = "", ref: str = "", raw: Any = None) -> None:
        typed_hits.append(
            {
                "chip": chip,
                "title": title,
                "subtitle": subtitle,
                "ref": ref,
                "raw": raw,
            }
        )

    # Prefer detected type as leading chip hit when query looks like wallet/token/protocol
    if detected.ok and detected.entity_type == "wallet":
        _add("Wallet", detected.normalized, "Public address · ANALYSE →", detected.normalized)
    elif detected.ok and detected.entity_type == "token":
        _add("Token", detected.normalized, "Token / market path · ANALYSE →", detected.normalized)
    elif detected.ok and detected.entity_type == "protocol":
        _add("Protocol", detected.normalized, "Protocol research · ANALYSE →", detected.normalized)
    elif detected.ok and detected.entity_type == "contract":
        _add("Contract", detected.normalized, "Contract hint · ANALYSE →", detected.normalized)

    for p in cats.get("projects") or []:
        _add("Project", p.get("name") or f"#{p.get('id')}", f"{p.get('stage') or p.get('status')} · {p.get('chain')}", str(p.get("id")), p)
    for a in cats.get("airdrops") or []:
        _add("Airdrop", a.get("project_name") or f"#{a.get('id')}", f"{a.get('status')} · {a.get('chain')}", str(a.get("id")), a)
    for w in cats.get("wallets") or []:
        _add("Wallet", w.get("label") or "wallet", str(w.get("address") or ""), str(w.get("id")), w)
    for e in cats.get("exchanges") or []:
        _add("Protocol", e.get("name") or "exchange", f"{e.get('type')} · {e.get('region')}", str(e.get("id")), e)
    for r in cats.get("rwa") or []:
        name = r.get("display_name") or r.get("project_name") or "RWA"
        demo = "DEMO" if r.get("is_demo") else ""
        _add("Project", name, f"RWA · {r.get('rwa_category')} {demo}".strip(), str(r.get("id") or name), r)

    return {
        "detected": detected.to_dict(),
        "categories": cats,
        "typed_hits": typed_hits,
        "total_category_hits": sum(len(v) for v in cats.values()),
    }


def homepage_search_placeholder() -> str:
    return "Search wallet, token, contract, project, protocol or airdrop..."


# Re-export detect for callers that only need the report detector
__all__ = [
    "ENTITY_CHIPS",
    "DetectedEntity",
    "analyse_session_payload",
    "chip_for_entity",
    "detect_entity_type",
    "detect_search_entity",
    "homepage_search_placeholder",
    "unified_search_results",
]
