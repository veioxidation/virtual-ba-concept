from __future__ import annotations

from typing import Dict, List, Optional

from typing_extensions import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class WorkflowState(TypedDict, total=False):
    """State shared between the LangGraph nodes for the Virtual BA workflow."""

    # Core identifiers describing the project and optional ARIS process.
    project_id: int
    project_name: NotRequired[str]
    process_id: NotRequired[Optional[int]]

    # Snapshot of high level metadata passed to the LLM for context.
    process_metadata: NotRequired[Dict[str, object]]

    # Placeholder BPMN JSON generated from the ARIS process ingestion step.
    bpmn_json: NotRequired[Dict[str, object]]

    # Generated report content (four structured sections) and persistence info.
    report_sections: NotRequired[Dict[str, str]]
    report_id: NotRequired[Optional[int]]
    report_ready: NotRequired[bool]

    # Cached response for convenience and the incremental message history.
    last_response: NotRequired[str]
    messages: Annotated[List[AnyMessage], add_messages]

