from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sse_starlette import EventSourceResponse


router = APIRouter(prefix="/workflows", tags=["workflows"])

# Only one workflow is currently exposed from this service.
WORKFLOW_NAME = "virtual-ba"

# Graph compiled at startup in lifespan and stored on app.state


def _graph(request: Request):
    """Pull the compiled graph instance from the FastAPI application state."""
    g = request.app.state.graph
    if not g:
        raise HTTPException(500, "Graph not initialized")
    return g


def _ensure_workflow(name: str) -> None:
    """Fail fast if a client tries to access an unknown workflow."""
    if name != WORKFLOW_NAME:
        raise HTTPException(404, f"Workflow '{name}' is not configured")


@router.get("/{name}/state")
async def get_state(
    name: str,
    request: Request,
    thread_id: str = Query(..., description="LangGraph thread id"),
):
    _ensure_workflow(name)
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = graph.get_state(config=cfg)
    # Snapshot contains raw LangGraph objects; run everything through the
    # serializer so the API returns JSON primitives only.
    return {
        "values": _serialize(snap.values),
        "next": snap.next,
        "created_at": snap.created_at,
    }


@router.post("/{name}/invoke")
async def invoke(
    name: str,
    request: Request,
    payload: dict,
    thread_id: str = Query("default"),
):
    _ensure_workflow(name)
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    prepared = _prepare_payload(payload)
    out = await graph.ainvoke(prepared, config=cfg)
    # Return only primitive values so clients do not need to import LangChain.
    return _serialize(out)


@router.post("/{name}/stream")
async def stream(
    name: str,
    request: Request,
    payload: dict,
    thread_id: str = Query("default"),
    modes: list[str] = Query(["updates", "messages", "custom"]),
):
    _ensure_workflow(name)
    graph = _graph(request)
    cfg = {"configurable": {"thread_id": thread_id}}
    prepared = _prepare_payload(payload)


    async def event_gen(req: Request):
        try:
            async for item in graph.astream(prepared, config=cfg, stream_mode=modes):
                if await req.is_disconnected():
                    break
                # item may be a tuple (mode, chunk) or a single chunk depending on stream_mode
                if isinstance(item, tuple) and len(item) == 2:
                    mode, chunk = item
                    payload_obj = {"mode": mode, "data": _serialize(chunk)}
                else:
                    payload_obj = {"mode": modes[0], "data": _serialize(item)}
                yield {"event": "update", "data": json.dumps(payload_obj)}
        except asyncio.CancelledError:
            raise


    return EventSourceResponse(event_gen(request), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# naive serializer for SSE JSON
def _prepare_payload(payload: dict) -> dict:
    """Normalise incoming request payloads so the graph can consume them."""
    prepared = deepcopy(payload) if payload else {}
    if "messages" in prepared:
        # Coerce plain dicts (as typically sent from clients) into LangChain
        # message objects understood by the graph.
        prepared["messages"] = [_coerce_message(msg) for msg in prepared["messages"]]
    return prepared


ROLE_TO_MESSAGE = {
    "user": HumanMessage,
    "human": HumanMessage,
    "assistant": AIMessage,
    "ai": AIMessage,
    "system": SystemMessage,
}

TYPE_TO_ROLE = {
    "human": "user",
    "ai": "assistant",
    "system": "system",
}


def _coerce_message(entry: Any) -> BaseMessage:
    """Convert a user-supplied message representation into a LangChain object."""
    if isinstance(entry, BaseMessage):
        return entry
    if not isinstance(entry, dict):
        raise ValueError("Messages must be BaseMessage objects or dicts")
    role = entry.get("role") or entry.get("type")
    if not role:
        raise ValueError("Message dict must include a role or type field")
    role = str(role).lower()
    message_cls = ROLE_TO_MESSAGE.get(role)
    if not message_cls:
        raise ValueError(f"Unsupported message role: {role}")
    content = entry.get("content", "")
    additional_kwargs = entry.get("additional_kwargs") or {}
    return message_cls(content=content, additional_kwargs=additional_kwargs)


def _message_to_dict(msg: BaseMessage) -> dict:
    """Serialise LangChain message objects back into primitive payloads."""
    data = {
        "role": TYPE_TO_ROLE.get(msg.type, msg.type),
        "content": msg.content,
    }
    if msg.additional_kwargs:
        data["additional_kwargs"] = msg.additional_kwargs
    return data


def _serialize(x: Any):
    """Best-effort conversion of LangChain artefacts into JSON primitives."""
    try:
        if isinstance(x, BaseMessage):
            return _message_to_dict(x)
        if isinstance(x, list):
            return [_serialize(item) for item in x]
        if isinstance(x, dict):
            return {key: _serialize(value) for key, value in x.items()}
        if hasattr(x, "model_dump"):
            return x.model_dump()
        return json.loads(json.dumps(x, default=str))
    except Exception:
        return str(x)
