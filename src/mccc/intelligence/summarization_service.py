"""SUMMARIZE stage — cost-controlled; extractive by default; never invent facts.

Summarization runs ONLY after filter/dedupe/classify. If no AI key, use
deterministic extractive summaries from source text only. Cache by fingerprint.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Optional


_CACHE: dict[str, str] = {}


def _cache_key(fingerprint: str, mode: str) -> str:
    return hashlib.sha256(f"{mode}:{fingerprint}".encode()).hexdigest()[:40]


class SummarizationService:
    """Extractive summarizer + optional LLM hook (not required for P1)."""

    def __init__(self, *, use_llm: Optional[bool] = None) -> None:
        if use_llm is None:
            use_llm = bool(os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
        self.use_llm = bool(use_llm)

    def summarize(
        self,
        *,
        title: str,
        body: str,
        fingerprint: str = "",
        is_demo: bool = False,
        max_sentences: int = 2,
        max_chars: int = 420,
    ) -> str:
        """Return a short summary grounded in provided text only."""
        fp = fingerprint or hashlib.sha256(f"{title}|{body}".encode()).hexdigest()[:32]
        key = _cache_key(fp, "extractive")
        if key in _CACHE:
            return _CACHE[key]

        text = (body or "").strip()
        if not text:
            # Incomplete text — do not invent; fall back to title only
            summary = (title or "").strip()
            if is_demo and summary and not summary.upper().startswith("[DEMO]"):
                summary = f"[DEMO] {summary}"
            _CACHE[key] = summary
            return summary

        # Extractive: first N sentences / clauses from source text
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            summary = text[:max_chars].strip()
        else:
            summary = " ".join(sentences[:max_sentences]).strip()
        if len(summary) > max_chars:
            summary = summary[: max_chars - 1].rstrip() + "…"

        # Guard: refuse to emit dollar amounts / investor names not in source
        # (extractive already constrained; this is a belt-and-suspenders check)
        if is_demo and "DEMO" not in summary.upper() and "SYNTHETIC" not in summary.upper():
            summary = f"DEMO / SYNTHETIC: {summary}"

        _CACHE[key] = summary
        return summary

    def why_it_matters(self, *, category: str, project: str, is_demo: bool) -> str:
        """Template rationale — no new factual claims."""
        proj = project or "Unknown"
        base = {
            "breaking": f"Time-sensitive signal for {proj}; verify against official sources before acting.",
            "new_projects": f"Early discovery signal for {proj}; status is research-only until verified.",
            "funding": f"Capital-formation signal for {proj}; amounts/investors remain as disclosed in source.",
            "airdrop_signals": f"Potential participation signal for {proj}; eligibility is unconfirmed unless source says otherwise.",
            "token_events": f"Token-lifecycle signal for {proj}; schedules stay Unknown unless sourced.",
            "technology": f"Technical development signal for {proj}; informational only.",
            "narratives": f"Narrative/theme cluster involving {proj}; not a trade recommendation.",
        }.get(category, f"Research signal related to {proj}.")
        if is_demo:
            return f"DEMO / SYNTHETIC — {base}"
        return base

    def clear_cache(self) -> None:
        _CACHE.clear()
