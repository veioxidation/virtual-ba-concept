from __future__ import annotations

from langchain.chat_models import init_chat_model

from app.core.config import settings
from app.workflows.models import LLM_MODELS

# Using LangChain's new init_chat_model wrapper keeps vendor-agnostic imports
# while enabling token streaming with LangGraph.

def chat_model():
    """Instantiate the chat model configured for the current environment."""
    model_name = LLM_MODELS.get(settings.llm_model, LLM_MODELS["openai"])
    return init_chat_model(model=model_name)

