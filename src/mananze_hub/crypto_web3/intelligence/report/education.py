"""Education helpers for Intelligence Reports — metric explainers + modes."""
from __future__ import annotations

from typing import Any

from mccc.intelligence.report.schema import METRIC_EXPLAINERS


def explain_metric(key: str) -> dict[str, str]:
    k = (key or "").strip().lower()
    # allow balance_eth → balance
    base = k.split("_")[0] if k.startswith("balance_") else k
    if base in METRIC_EXPLAINERS:
        return dict(METRIC_EXPLAINERS[base])
    if k in METRIC_EXPLAINERS:
        return dict(METRIC_EXPLAINERS[k])
    return {
        "what": f"Metric `{key}` as observed in this report.",
        "why": "Included when a provider or local research store supplies it.",
        "cannot": "A single metric cannot tell you what to buy or sell — research only.",
    }


def render_explainer_markdown(key: str) -> str:
    e = explain_metric(key)
    return (
        f"**What it is:** {e['what']}\n\n"
        f"**Why researchers look at it:** {e['why']}\n\n"
        f"**What it cannot tell you:** {e['cannot']}"
    )


def mode_copy(beginner_mode: bool) -> dict[str, str]:
    if beginner_mode:
        return {
            "label": "Beginner Mode",
            "blurb": (
                "Plain language first. Advanced technical fields are collapsed. "
                "Still public-data only — never paste seeds or private keys."
            ),
        }
    return {
        "label": "Advanced Mode",
        "blurb": (
            "Shows provenance (source, timestamp, chain, definition), verification level, "
            "and raw snapshot keys for diligence."
        ),
    }


def journey_steps() -> list[dict[str, str]]:
    return [
        {"step": "Search", "detail": "Find a wallet, token, contract, project, protocol, or RWA entity."},
        {"step": "Analyse", "detail": "Run an Intelligence Report over public / labelled data."},
        {"step": "Understand", "detail": "Read beginner + advanced explanations with confidence."},
        {"step": "Investigate", "detail": "Follow Sources and risk language — no buy/sell instructions."},
    ]
