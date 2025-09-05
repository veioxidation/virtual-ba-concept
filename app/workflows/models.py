"""Registry of chat models available for workflows."""

from __future__ import annotations

from typing import Dict

LLM_MODELS: Dict[str, str] = {
    "openai": "openai:gpt-4o-mini",
    "azure": "azure:gpt-4o-mini",
}

