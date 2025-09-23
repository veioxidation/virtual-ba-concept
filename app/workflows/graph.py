from __future__ import annotations

import json
import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.db.session import AsyncSessionMaker
from app.models.project import Project
from app.models.process import Process
from app.repositories.report import ReportRepository
from app.workflows.llm import chat_model
from app.workflows.state import WorkflowState

logger = logging.getLogger(__name__)


class ProcessReportSections(BaseModel):
    """Structured report schema enforced through LangChain output parsing."""

    model_config = ConfigDict(populate_by_name=True)

    process_overview: str = Field(
        ...,
        alias="Process Overview",
        description="A general overview about the process.",
    )
    automation_opportunities: str = Field(
        ...,
        alias="Automation opportunities",
        description="Potential automation opportunities identified within the process.",
    )
    data_quality_issues: str = Field(
        ...,
        alias="Data Quality issues",
        description="Potential data quality issues observed in the process map or supporting data.",
    )
    questions: str = Field(
        ...,
        alias="Questions",
        description="Questions to ask SMEs to better understand the process.",
    )


FIELD_TO_ALIAS = {
    name: field.alias or name for name, field in ProcessReportSections.model_fields.items()
}
ALIAS_TO_FALLBACK = {
    (field.alias or name): field.description or ""
    for name, field in ProcessReportSections.model_fields.items()
}


async def _load_project_context(project_id: int) -> tuple[Project, Process | None]:
    """Fetch the project and (if present) the related ARIS process."""

    # Each node that needs DB access opens its own session so the graph remains
    # stateless between invocations.
    async with AsyncSessionMaker() as session:
        project = await session.get(Project, project_id)
        if project is None:
            raise ValueError(f"Project {project_id} was not found")

        process: Process | None = None
        if project.process_id:
            process = await session.get(Process, project.process_id)

    return project, process


def _build_bpmn_placeholder(project: Project, process: Process | None) -> Dict[str, Any]:
    """Placeholder conversion for ARIS → BPMN JSON."""

    # The ARIS → BPMN conversion is handled elsewhere; for now we return a
    # structure that mirrors the expected shape so downstream prompts remain the
    # same once the real converter is wired in.
    return {
        "process_id": process.id if process else None,
        "project_id": project.id,
        "name": (process.name if process else project.name) or f"Project {project.id}",
        "description": (
            process.description
            if process and process.description
            else project.description
        ),
        "lanes": [],
        "events": [],
        "tasks": [],
    }


def _normalise_sections(raw_sections: Any) -> Dict[str, str]:
    """Ensure the four canonical report sections are always present."""

    sections: Dict[str, str] = {}

    if isinstance(raw_sections, ProcessReportSections):
        sections = raw_sections.model_dump(by_alias=True)
    elif isinstance(raw_sections, dict):
        lower = {str(k).lower(): v for k, v in raw_sections.items()}
        sections = {}
        for field_name, alias in FIELD_TO_ALIAS.items():
            candidate = lower.get(alias.lower(), lower.get(field_name.lower(), ""))
            if isinstance(candidate, str):
                sections[alias] = candidate.strip()
            elif candidate is None:
                sections[alias] = ""
            else:
                sections[alias] = str(candidate).strip()
    elif isinstance(raw_sections, str):
        paragraphs = [p.strip() for p in raw_sections.split("\n\n") if p.strip()]
        for idx, alias in enumerate(FIELD_TO_ALIAS.values()):
            sections[alias] = paragraphs[idx] if idx < len(paragraphs) else ""

    for alias, fallback in ALIAS_TO_FALLBACK.items():
        if not sections.get(alias):
            sections[alias] = fallback

    return sections


async def bootstrap_context(
    state: WorkflowState, config: RunnableConfig
) -> WorkflowState:
    """Initial node: resolve the project and load any existing report."""

    writer = get_stream_writer()
    project_ref = config.get("configurable", {}).get("thread_id")
    if project_ref is None:
        raise ValueError("thread_id is required and should correspond to a project id")

    try:
        project_id = int(project_ref)
    except (TypeError, ValueError) as exc:
        raise ValueError("thread_id must be an integer project id") from exc

    project, process = await _load_project_context(project_id)
    writer({"event": "bootstrap", "status": "loaded_project"})

    update: WorkflowState = {
        "project_id": project_id,
        "project_name": project.name,
        "process_id": project.process_id,
        "process_metadata": {
            "process_name": process.name if process else project.name,
            "process_description": process.description if process else project.description,
        },
    }

    # If this thread already generated a report we restore it so later nodes can
    # short-circuit.
    async with AsyncSessionMaker() as session:
        repo = ReportRepository(session)
        existing = await repo.get_by_thread_id(str(project_ref))
        if existing:
            update["report_id"] = existing.id
            update["report_sections"] = _normalise_sections(existing.sections)
            update["report_ready"] = True
            writer({"event": "bootstrap", "status": "report_loaded"})

    return update


async def load_process_model(
    state: WorkflowState, config: RunnableConfig
) -> WorkflowState:
    """Generate (or reuse) the BPMN JSON representation for the project."""

    if state.get("bpmn_json"):
        return {}

    project_id = state.get("project_id")
    if project_id is None:
        return {}

    project, process = await _load_project_context(project_id)
    bpmn_json = _build_bpmn_placeholder(project, process)

    writer = get_stream_writer()
    writer({"event": "process", "status": "bpmn_ready"})
    return {
        "bpmn_json": bpmn_json,
        "process_metadata": {
            "process_name": bpmn_json["name"],
            "process_description": bpmn_json.get("description"),
        },
    }


async def generate_process_report(
    state: WorkflowState, config: RunnableConfig
) -> WorkflowState:
    """Call the LLM to produce a structured four-section report."""

    if state.get("report_ready"):
        return {}

    bpmn_json = state.get("bpmn_json")
    if not bpmn_json:
        return {}

    llm = chat_model()
    writer = get_stream_writer()
    writer({"event": "report", "status": "generating"})

    messages = [
        SystemMessage(
            content=(
                "You are an expert business analyst. Given a BPMN JSON structure, "
                "produce an analytical report summarising the process."
            )
        ),
        HumanMessage(
            content=(
                "Fill the structured process report using the BPMN JSON below. "
                "Each field should be a concise paragraph tailored to senior "
                "stakeholders.\n\n"
                f"BPMN JSON:\n{json.dumps(bpmn_json, indent=2, default=str)}"
            )
        ),
    ]

    structured_llm = llm.with_structured_output(ProcessReportSections)
    raw_sections: Any
    try:
        raw_sections = await structured_llm.ainvoke(messages, config=config)
    except Exception:
        logger.exception(
            "Structured report generation failed; falling back to text parsing",
        )
        response = await llm.ainvoke(messages, config=config)
        raw_sections = response.content

    sections = _normalise_sections(raw_sections)
    writer({"event": "report", "status": "ready"})

    return {
        "report_sections": sections,
        "report_ready": True,
    }


async def persist_report(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
    """Insert or update the report record so future runs can reuse it."""

    if not state.get("report_ready") or not state.get("report_sections"):
        return {}

    project_id = state.get("project_id")
    if project_id is None:
        return {}

    thread_ref = config.get("configurable", {}).get("thread_id")
    thread_id = str(thread_ref) if thread_ref is not None else None

    # Persist within its own session to avoid cross-node transaction coupling.
    async with AsyncSessionMaker() as session:
        repo = ReportRepository(session)
        sections = _normalise_sections(state["report_sections"])

        if state.get("report_id"):
            await repo.update_sections(state["report_id"], sections)
            await session.commit()
            report_id = state["report_id"]
        else:
            title = f"{state.get('project_name', 'Process')} analysis"
            report = await repo.create(
                project_id=project_id,
                title=title,
                sections=sections,
                thread_id=thread_id,
            )
            await session.commit()
            report_id = report.id

    return {"report_id": report_id, "report_ready": True}


async def answer_question(state: WorkflowState, config: RunnableConfig) -> WorkflowState:
    """Final node: respond to the latest user question using stored context."""

    messages = state.get("messages", [])
    question = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            question = msg.content
            break

    if not question:
        question = (
            "Provide a concise summary of the process and highlight the "
            "main risks and next steps."
        )

    context_blob = {
        "process": state.get("process_metadata", {}),
        "bpmn": state.get("bpmn_json", {}),
        "report": state.get("report_sections", {}),
    }

    llm = chat_model()
    response = await llm.ainvoke(
        [
            SystemMessage(
                content=(
                    "You are a virtual business analyst. Answer the user's "
                    "question using only the provided process report and BPMN "
                    "information."
                )
            ),
            HumanMessage(
                content=(
                    "Process information:\n"
                    + json.dumps(context_blob, indent=2, default=str)
                    + "\n\nUser question: "
                    + question
                )
            ),
        ],
        config=config,
    )

    ai_message = AIMessage(content=response.content)
    return {"messages": [ai_message], "last_response": response.content}


def build_graph():
    """Assemble the LangGraph workflow for project analysis."""

    builder = StateGraph(WorkflowState)
    # Each node corresponds to one phase of the workflow.
    builder.add_node("bootstrap", bootstrap_context)
    builder.add_node("process_model", load_process_model)
    builder.add_node("report", generate_process_report)
    builder.add_node("persist", persist_report)
    builder.add_node("respond", answer_question)

    # Simple linear graph: bootstrap → process → report → persist → respond.
    builder.add_edge(START, "bootstrap")
    builder.add_edge("bootstrap", "process_model")
    builder.add_edge("process_model", "report")
    builder.add_edge("report", "persist")
    builder.add_edge("persist", "respond")
    builder.add_edge("respond", END)
    return builder
