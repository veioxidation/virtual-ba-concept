"""Registry of chat models available for workflows."""

from __future__ import annotations

from typing import Dict

# TODO - expand model definition
LLM_MODELS: Dict[str, str] = {
    "openai": "openai:gpt-4o",
    "azure": "azure:gpt-4o",
}

