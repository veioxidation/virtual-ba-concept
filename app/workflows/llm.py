from __future__ import annotations

from langchain.chat_models import init_chat_model


# Using LangChain's init_chat_model wrapper keeps vendor-agnostic imports while
# enabling token streaming with LangGraph.

def chat_model():
    """Instantiate the default chat model configured for LangGraph usage."""

    # Configure via env vars, e.g. OPENAI_API_KEY; replace with azure, groq, etc.
    return init_chat_model(model="openai:gpt-4o-mini")
