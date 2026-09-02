"""AI research assistant — AssistantProvider abstraction (rule + OpenAI-compatible).

Never invent live prices. Refuse secrets. Label FACT / DATA / ANALYSIS / SPECULATION.
Log ai_usage on every answer path.
"""
from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable

from mccc.assistant import match_tips, structure_research_note
from mccc.db import connect, utc_now

SECRET_PATTERNS = (
    r"\bseed\s*phrase\b",
    r"\bmnemonic\b",
    r"\bprivate\s*key\b",
    r"\bprivkey\b",
    r"\brecovery\s*phrase\b",
    r"\bsecret\s*key\b",
)

REFUSAL = (
    "I will not accept, store, or reason about seed phrases or private keys. "
    "Keep secrets offline — MCCC is research-only."
)

UNAVAILABLE = "Information unavailable"

RESEARCH_CHECKLIST = [
    "Define the open question and success criteria",
    "Collect primary sources (docs, explorer, audits) with dates",
    "Map token / governance / upgrade risks",
    "Separate FACT / DATA / ANALYSIS / SPECULATION in notes",
    "Check LIVE vs DEMO before using any market number",
    "Never paste seeds, private keys, or exchange 2FA into tools",
    "Record next action + last_checked on the Project Tracker row",
]

_MARKET_QUERY_RE = re.compile(
    r"\b(price|prices|quote|quotes|market\s*cap|btc|eth|sol|usd|coingecko|ticker|spot)\b",
    re.IGNORECASE,
)


def contains_secrets(text: str) -> bool:
    from mccc.security import is_sensitive_credential

    if is_sensitive_credential(text or ""):
        return True
    lowered = text or ""
    for pat in SECRET_PATTERNS:
        if re.search(pat, lowered, flags=re.IGNORECASE):
            return True
    return False


def _label(kind: str, body: str) -> str:
    return f"[{kind}] {body}"


def looks_like_market_question(query: str) -> bool:
    return bool(_MARKET_QUERY_RE.search(query or ""))


def market_context_block() -> str:
    """Pull labelled prices from market_provider — never invent numbers."""
    try:
        from mccc.market_provider import get_default_provider

        provider = get_default_provider()
        pmap, source, is_live = provider.price_map()
        tag = "LIVE" if is_live else "DEMO"
        if not pmap:
            return _label(
                "DATA",
                f"Live quotes: {UNAVAILABLE} (provider returned empty). Source={source} · mode={tag}.",
            )
        # Show a short sample only — labelled
        sample = ", ".join(f"{k}={v}" for k, v in list(pmap.items())[:8])
        return _label(
            "DATA",
            f"market_provider [{tag}] source={source}: {sample}. "
            f"Do not treat DEMO as live. Full table: Markets page.",
        )
    except Exception:
        return _label("DATA", f"Live quotes: {UNAVAILABLE} (market_provider error).")


def research_template(topic: str, context: str = "") -> dict[str, Any]:
    """Structured research note with explicit uncertainty markers."""
    base = structure_research_note(topic, context)
    body = base["body"]
    body += (
        f"\n## Labels\n"
        f"- {_label('FACT', 'Only claim what you verified from primary sources.')}\n"
        f"- {_label('DATA', 'Attach numbers with source + timestamp; otherwise mark unavailable.')}\n"
        f"- {_label('ANALYSIS', 'Interpretations of verified facts/data.')}\n"
        f"- {_label('SPECULATION', 'Unverified hypotheses — never present as live facts.')}\n"
        f"\n## Live market quotes\n- {UNAVAILABLE} unless Market APIs returns is_live=True.\n"
        f"\n## Research checklist\n"
        + "\n".join(f"- [ ] {item}" for item in RESEARCH_CHECKLIST)
        + "\n"
    )
    base["body"] = body
    return base


@runtime_checkable
class AssistantProvider(Protocol):
    """Provider interface for research answers."""

    name: str

    def answer(self, query: str) -> dict[str, Any]:
        ...


class BaseAssistantProvider(ABC):
    name: str = "base"

    @abstractmethod
    def answer(self, query: str) -> dict[str, Any]:
        raise NotImplementedError


class RuleBasedProvider(BaseAssistantProvider):
    """Local rule / tip matcher — default when no API key."""

    name = "rule"

    def answer(self, query: str) -> dict[str, Any]:
        if contains_secrets(query):
            return {
                "mode": "refusal",
                "is_llm": False,
                "provider": self.name,
                "answer": REFUSAL,
                "labels": ["FACT"],
                "tips": [],
            }
        tips = match_tips(query)
        sections = []
        sections.append(
            _label("FACT", "MCCC local assistant is rule-based and does not invent live prices.")
        )
        if looks_like_market_question(query):
            sections.append(market_context_block())
        else:
            sections.append(
                _label(
                    "DATA",
                    f"Live quotes: {UNAVAILABLE} from this path unless you ask a market question "
                    "(then market_provider is used with LIVE/DEMO labels).",
                )
            )
        for tip in tips:
            sections.append(_label("ANALYSIS", f"{tip['title']}:\n{tip['body']}"))
        sections.append(
            _label(
                "SPECULATION",
                "Any narrative beyond the checklist above is unverified — treat as research only.",
            )
        )
        sections.append(
            _label("FACT", "Research checklist:\n" + "\n".join(f"- {i}" for i in RESEARCH_CHECKLIST[:5]))
        )
        return {
            "mode": "rule_based",
            "is_llm": False,
            "provider": self.name,
            "answer": "\n\n".join(sections),
            "labels": ["FACT", "DATA", "ANALYSIS", "SPECULATION"],
            "tips": tips,
        }


class OpenAICompatibleProvider(BaseAssistantProvider):
    """Optional OpenAI-compatible chat API via AI_API_KEY / AI_API_BASE / AI_MODEL."""

    name = "openai_compatible"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else os.environ.get("AI_API_KEY", "")).strip()
        self.base_url = (
            base_url if base_url is not None else os.environ.get("AI_API_BASE", "https://api.openai.com/v1")
        ).strip()
        self.model = (model if model is not None else os.environ.get("AI_MODEL", "gpt-4o-mini")).strip()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _chat(self, query: str) -> Optional[str]:
        try:
            import requests

            url = self.base_url.rstrip("/") + "/chat/completions"
            market_hint = ""
            if looks_like_market_question(query):
                market_hint = "\n" + market_context_block()
            system = (
                "You are MCCC research assistant. Never invent live prices or claim DEMO data is live. "
                "Refuse any seed phrase / private key content. "
                "Prefix statements with FACT, DATA, ANALYSIS, or SPECULATION. "
                f"If unsure of a number or status, say '{UNAVAILABLE}'."
                f"{market_hint}"
            )
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": query},
                ],
                "temperature": 0.2,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def answer(self, query: str) -> dict[str, Any]:
        if contains_secrets(query):
            return {
                "mode": "refusal",
                "is_llm": False,
                "provider": self.name,
                "answer": REFUSAL,
                "labels": ["FACT"],
                "tips": [],
            }
        if not self.available:
            return RuleBasedProvider().answer(query)
        content = self._chat(query)
        if not content:
            fallback = RuleBasedProvider().answer(query)
            fallback["provider"] = f"{self.name}->rule"
            return fallback
        return {
            "mode": "llm",
            "is_llm": True,
            "provider": self.name,
            "answer": content,
            "labels": ["FACT", "DATA", "ANALYSIS", "SPECULATION"],
            "tips": match_tips(query),
        }


def get_assistant_provider(prefer_llm: bool = True) -> BaseAssistantProvider:
    """Factory: OpenAI-compatible when key present and prefer_llm, else rule-based."""
    llm = OpenAICompatibleProvider()
    if prefer_llm and llm.available:
        return llm
    return RuleBasedProvider()


def rule_based_answer(query: str) -> dict[str, Any]:
    return RuleBasedProvider().answer(query)


def _openai_compatible_chat(query: str, api_key: str, base_url: str, model: str) -> Optional[str]:
    """Legacy helper retained for tests / direct callers."""
    return OpenAICompatibleProvider(api_key=api_key, base_url=base_url, model=model)._chat(query)


def log_ai_usage(
    kind: str = "chat",
    tokens_est: int = 0,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO ai_usage (user_id, kind, tokens_est, created_at) VALUES (?, ?, ?, ?)",
            (user_id, kind, int(tokens_est or 0), utc_now()),
        )


def answer(
    query: str,
    *,
    use_llm: bool = True,
    user_id: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Main entry: refuse secrets; try optional LLM if AI_API_KEY set; else rule-based."""
    q = (query or "").strip()
    if contains_secrets(q):
        log_ai_usage("refusal", 0, user_id=user_id, db_path=db_path)
        return {
            "mode": "refusal",
            "is_llm": False,
            "provider": "security",
            "answer": REFUSAL,
            "labels": ["FACT"],
            "tips": [],
        }

    provider = get_assistant_provider(prefer_llm=use_llm)
    result = provider.answer(q)
    mode = result.get("mode", "rule_based")
    if mode == "refusal":
        log_ai_usage("refusal", 0, user_id=user_id, db_path=db_path)
    elif mode == "llm":
        tokens_est = max(1, len(q.split()) + len(str(result.get("answer", "")).split()))
        log_ai_usage("llm", tokens_est, user_id=user_id, db_path=db_path)
    else:
        log_ai_usage("rule_based", len(q.split()), user_id=user_id, db_path=db_path)
    return result
