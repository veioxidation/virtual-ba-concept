from __future__ import annotations

from operator import add
from typing import TypedDict

from typing_extensions import Annotated


class WorkflowState(TypedDict, total=False):
    """State shared across workflow nodes.

    `messages` accumulates conversation turns. `process` holds the BPMN JSON
    describing the business process. `report` stores the generated analysis
    sections for downstream use.
    """

    messages: Annotated[list[dict], add]
    process: dict | None
    report: dict | None
