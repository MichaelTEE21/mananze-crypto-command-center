"""AI research assistant — rule-based by default; optional OpenAI-compatible API.

Never invent live prices. Refuse secrets. Label FACT / DATA / ANALYSIS / SPECULATION.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

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


def contains_secrets(text: str) -> bool:
    lowered = text or ""
    for pat in SECRET_PATTERNS:
        if re.search(pat, lowered, flags=re.IGNORECASE):
            return True
    return False


def _label(kind: str, body: str) -> str:
    return f"[{kind}] {body}"


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
    )
    base["body"] = body
    return base


def rule_based_answer(query: str) -> dict[str, Any]:
    if contains_secrets(query):
        return {
            "mode": "refusal",
            "is_llm": False,
            "answer": REFUSAL,
            "labels": ["FACT"],
            "tips": [],
        }
    tips = match_tips(query)
    sections = []
    sections.append(_label("FACT", "MCCC local assistant is rule-based and does not invent live prices."))
    sections.append(
        _label("DATA", f"Live quotes: {UNAVAILABLE} from this path — use Market APIs with is_live check.")
    )
    for tip in tips:
        sections.append(_label("ANALYSIS", f"{tip['title']}:\n{tip['body']}"))
    sections.append(
        _label("SPECULATION", "Any narrative beyond the checklist above is unverified — treat as research only.")
    )
    return {
        "mode": "rule_based",
        "is_llm": False,
        "answer": "\n\n".join(sections),
        "labels": ["FACT", "DATA", "ANALYSIS", "SPECULATION"],
        "tips": tips,
    }


def _openai_compatible_chat(query: str, api_key: str, base_url: str, model: str) -> Optional[str]:
    try:
        import requests

        url = base_url.rstrip("/") + "/chat/completions"
        system = (
            "You are MCCC research assistant. Never invent live prices or claim DEMO data is live. "
            "Refuse any seed phrase / private key content. "
            "Prefix statements with FACT, DATA, ANALYSIS, or SPECULATION. "
            f"If unsure of a number or status, say '{UNAVAILABLE}'."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


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
            "answer": REFUSAL,
            "labels": ["FACT"],
            "tips": [],
        }

    api_key = os.environ.get("AI_API_KEY", "").strip()
    if use_llm and api_key:
        base = os.environ.get("AI_API_BASE", "https://api.openai.com/v1").strip()
        model = os.environ.get("AI_MODEL", "gpt-4o-mini").strip()
        content = _openai_compatible_chat(q, api_key, base, model)
        if content:
            tokens_est = max(1, len(q.split()) + len(content.split()))
            log_ai_usage("llm", tokens_est, user_id=user_id, db_path=db_path)
            return {
                "mode": "llm",
                "is_llm": True,
                "answer": content,
                "labels": ["FACT", "DATA", "ANALYSIS", "SPECULATION"],
                "tips": match_tips(q),
            }

    result = rule_based_answer(q)
    log_ai_usage("rule_based", len(q.split()), user_id=user_id, db_path=db_path)
    return result
