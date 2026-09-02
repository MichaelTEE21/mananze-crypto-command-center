"""AI service facade — AssistantProvider abstraction + ai_service public API."""
from __future__ import annotations

from mccc.ai_service import (
    REFUSAL,
    RESEARCH_CHECKLIST,
    UNAVAILABLE,
    AssistantProvider,
    BaseAssistantProvider,
    OpenAICompatibleProvider,
    RuleBasedProvider,
    answer,
    contains_secrets,
    get_assistant_provider,
    log_ai_usage,
    looks_like_market_question,
    market_context_block,
    research_template,
    rule_based_answer,
)

__all__ = [
    "REFUSAL",
    "RESEARCH_CHECKLIST",
    "UNAVAILABLE",
    "AssistantProvider",
    "BaseAssistantProvider",
    "OpenAICompatibleProvider",
    "RuleBasedProvider",
    "answer",
    "contains_secrets",
    "get_assistant_provider",
    "log_ai_usage",
    "looks_like_market_question",
    "market_context_block",
    "research_template",
    "rule_based_answer",
]
