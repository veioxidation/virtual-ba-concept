from __future__ import annotations

import json
from langgraph.graph import StateGraph, START, END

from app.workflows.state import WorkflowState
from app.workflows.llm import chat_model


def generate_report_node(state: WorkflowState):
    """Create a four-section report from a BPMN process description."""
    process = state.get("process", {})
    prompt = (
        "You are a virtual business analyst. Given the following process JSON, "
        "produce a report with four sections: Process Overview, Improvement "
        "Opportunities, Data Quality Issues, and Questions for Further Analysis. "
        "Return the result as a JSON object with keys 'overview', 'improvements', "
        "'data_quality', and 'questions'.\n" +
        f"Process: {json.dumps(process)}"
    )
    llm = chat_model()
    resp = llm.invoke([{"role": "user", "content": prompt}])
    try:
        sections = json.loads(resp.content)
    except Exception:  # pragma: no cover - fall back if model returns non-JSON
        sections = {
            "overview": resp.content,
            "improvements": "",
            "data_quality": "",
            "questions": "",
        }
    return {"report": sections}


def chat_node(state: WorkflowState):
    """Respond to user queries about the generated report."""
    report = state.get("report", {})
    messages = state.get("messages", [])
    llm = chat_model()
    system = {
        "role": "system",
        "content": "You are a helpful business analyst. Use the following report "
                   "as context:\n" + json.dumps(report),
    }
    resp = llm.invoke([system, *messages])
    return {"messages": [resp]}


def build_graph():
    builder = StateGraph(WorkflowState)
    builder.add_node("generate_report", generate_report_node)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "generate_report")
    builder.add_edge("generate_report", "chat")
    builder.add_edge("chat", END)
    return builder
