from __future__ import annotations
from typing import TypedDict
from typing_extensions import Annotated
from operator import add


# Minimal shared state for a demo graph. Extend with your own channels.
class WorkflowState(TypedDict):
    messages: Annotated[list[dict], add]
    summary: str