from __future__ import annotations
import operator
from typing import TypedDict
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer
from app.workflows.state import WorkflowState
from app.workflows.llm import chat_model


# Define nodes


def summarize_node(state: WorkflowState):
    """Toy example: summarise accumulated messages.
    Demonstrates custom streaming inside a node (stream_mode="custom").
    """
    writer = get_stream_writer()
    writer({"progress": "summarizing"})
    text = "\n".join([m["content"] for m in state.get("messages", [])])
    llm = chat_model()
    resp = llm.invoke([{"role": "user", "content": f"Summarize: {text}"}])
    return {"summary": resp.content}


# Build & compile graph (no checkpointer here; injected in app.lifespan)


def build_graph():
    builder = StateGraph(WorkflowState)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "summarize")
    builder.add_edge("summarize", END)
    return builder